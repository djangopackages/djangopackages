"""Local git checkouts of the packages we index, and the AST scan over them.

The checkouts live under ``settings.PACKAGE_REPO_ROOT``, one directory per
package slug, and are refreshed in place rather than re-cloned. Scanning
source tells us things the metadata cannot: which Django APIs a package
actually touches, rather than which ones its classifiers claim.
"""

from __future__ import annotations

import ast
import os
import subprocess
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlparse

from django.conf import settings
from django.db.models import Q

# Hosts we know how to clone from. Anything else is skipped rather than
# attempted, so a dead host does not cost us a network timeout per run.
CLONEABLE_HOSTS = frozenset(
    {
        "github.com",
        "gitlab.com",
        "bitbucket.org",
        "codeberg.org",
    }
)

# Directories that never hold a package's own source.
SKIP_DIRS = frozenset(
    {
        ".git",
        ".hg",
        ".svn",
        ".tox",
        ".nox",
        ".venv",
        "venv",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        "__pycache__",
        "node_modules",
        "site-packages",
        "build",
        "dist",
    }
)


class CheckoutError(RuntimeError):
    """A git command failed, or the repo cannot be cloned at all."""


@dataclass
class ScanResult:
    """What one scan of one checkout found."""

    usage: Counter[str] = field(default_factory=Counter)
    files_scanned: int = 0
    files_skipped: int = 0

    @property
    def symbols(self) -> int:
        return len(self.usage)

    @property
    def total(self) -> int:
        return sum(self.usage.values())


def is_cloneable(repo_url: str) -> bool:
    host = urlparse(repo_url or "").netloc.lower().removeprefix("www.")
    return host in CLONEABLE_HOSTS


def scannable_packages():
    """The packages worth keeping a checkout of.

    A repo we can clone from and a PyPI release, because a package with
    no release is usually an abandoned idea or someone's fork, and its
    imports say nothing about what the ecosystem actually depends on.
    Narrowing here rather than at the call site keeps sync and scan
    looking at the same set, so a scan cannot quietly cover less than
    the sync fetched.
    """
    from package.models import Package

    host_q = Q()
    for host in CLONEABLE_HOSTS:
        host_q |= Q(repo_url__icontains=host)

    return (
        Package.objects.exclude(repo_url="")
        .exclude(pypi_url="")
        .filter(host_q)
        # probe is the stored verdict from check_package_sources. Null
        # means undecided, which we take as "worth a try": a new package
        # should not have to wait for a check to be looked at.
        .exclude(probe=False)
        .order_by("-score", "title")
    )


def checkout_path(package) -> Path:
    """Where this package's checkout lives. One directory per slug."""
    return Path(settings.PACKAGE_REPO_ROOT) / package.slug


def _git(*args: str, cwd: Path | None = None, timeout: int = 300) -> str:
    """Run git with prompting disabled, so a private repo fails fast.

    Without these a clone of something we cannot read blocks forever
    waiting on credentials nobody is there to type.
    """
    env = os.environ | {
        "GIT_TERMINAL_PROMPT": "0",
        "GIT_ASKPASS": "",
        "GCM_INTERACTIVE": "never",
    }
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=cwd,
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except FileNotFoundError as exc:
        raise CheckoutError("git is not installed in this image") from exc
    except subprocess.TimeoutExpired as exc:
        raise CheckoutError(f"git {args[0]} timed out after {timeout}s") from exc

    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip().splitlines()
        raise CheckoutError(detail[-1] if detail else f"git {args[0]} failed")

    return result.stdout


def repo_is_reachable(repo_url: str, *, timeout: int = 30) -> tuple[bool, str]:
    """Ask the remote whether it exists, without downloading it.

    `git ls-remote` is a single request that returns the ref list, so a
    dead or private repo costs a round trip instead of a clone. At four
    thousand packages that is the difference between a pre-flight check
    and an afternoon.
    """
    if not is_cloneable(repo_url):
        return False, f"cannot clone from {repo_url or 'no repo url'}"

    try:
        _git("ls-remote", "--exit-code", repo_url, "HEAD", timeout=timeout)
    except CheckoutError as exc:
        detail = str(exc)
        # A host that wants credentials is telling us the repo is gone or
        # private; it cannot say which, because saying which would leak
        # the existence of private repos. Either way we cannot read it.
        if "could not read Username" in detail or "Authentication failed" in detail:
            return False, "repo is private or deleted"
        return False, detail
    return True, ""


def pypi_is_published(pypi_url: str, *, timeout: float = 10.0) -> tuple[bool, str]:
    """Whether PyPI still serves this project.

    A package can be delisted or renamed long after we recorded it, and
    the stored pypi_url is not evidence that anything is there now.
    """
    import httpx2

    from package.pypi import PyPIClient

    name = (pypi_url or "").strip().strip("/").rsplit("/", 1)[-1]
    if not name:
        return False, "no pypi url"

    url = PyPIClient().get_package_json_url(name)
    try:
        response = httpx2.head(url, timeout=timeout, follow_redirects=True)
    except httpx2.RequestError as exc:
        return False, f"pypi unreachable: {type(exc).__name__}"

    if response.status_code == 404:
        return False, "not on pypi"
    if response.status_code >= 400:
        return False, f"pypi returned {response.status_code}"
    return True, ""


def sync_checkout(package, *, depth: int = 1, timeout: int = 300) -> tuple[Path, str]:
    """Clone the package's repo, or bring an existing checkout up to date.

    Returns the path and what happened, "cloned" or "updated". Shallow by
    default: we only ever read the working tree, so history is weight we
    do not need across thousands of repos.
    """
    if not is_cloneable(package.repo_url):
        raise CheckoutError(f"cannot clone from {package.repo_url or 'no repo url'}")

    path = checkout_path(package)

    if (path / ".git").is_dir():
        # Reset rather than pull: the tree is ours to throw away, and a
        # merge conflict in a checkout nobody edits is not worth handling.
        _git("fetch", "--depth", str(depth), "origin", cwd=path, timeout=timeout)
        head = _git("rev-parse", "FETCH_HEAD", cwd=path, timeout=timeout).strip()
        _git("reset", "--hard", head, cwd=path, timeout=timeout)
        _git("clean", "-qfdx", cwd=path, timeout=timeout)
        return path, "updated"

    path.parent.mkdir(parents=True, exist_ok=True)
    _git(
        "clone",
        "--depth",
        str(depth),
        "--quiet",
        package.repo_url,
        str(path),
        timeout=timeout,
    )
    return path, "cloned"


def iter_python_files(root: Path):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in filenames:
            if name.endswith(".py"):
                yield Path(dirpath) / name


def scan_checkout(root: Path, packages: tuple[str, ...] = ("django",)) -> ScanResult:
    """Count which symbols from ``packages`` a checkout uses.

    The counting is django-probe's: a NodeVisitor that follows import
    aliasing, so ``from django.db import models`` and a later
    ``models.CharField`` resolve to the full dotted path rather than being
    matched as text.
    """
    from django_probe.usage import count_package_usage

    result = ScanResult()

    for path in iter_python_files(root):
        try:
            source = path.read_text(encoding="utf-8")
            tree = ast.parse(source)
        except (OSError, UnicodeDecodeError, SyntaxError, ValueError):
            # Other people's repos hold unparseable and non-UTF-8 files.
            # One bad file should not fail the package.
            result.files_skipped += 1
            continue

        result.usage.update(count_package_usage(tree, packages))
        result.files_scanned += 1

    return result
