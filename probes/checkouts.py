"""Local git checkouts of the packages we index, and the AST scan over them.

The checkouts live under ``settings.PACKAGE_REPO_ROOT``, one directory per
package slug, and are refreshed in place rather than re-cloned. Scanning
source tells us things the metadata cannot: which Django APIs a package
actually touches, rather than which ones its classifiers claim.
"""

from __future__ import annotations

import ast
import os
import shutil
import subprocess
import warnings
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlparse

from django.conf import settings
from django.db.models import Q

from probes.models import SETTINGS_PREFIX

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


# A .py file bigger than this is generated or vendored, not something
# anyone wrote, and parsing it costs more memory than it tells us.
MAX_FILE_BYTES = 2 * 1024 * 1024

# What git prints when the network let it down rather than the repo.
# Seeing one of these says nothing about whether the repo exists.
NETWORK_ERRORS = (
    "could not resolve host",
    "failed to connect",
    "connection timed out",
    "connection reset",
    "operation timed out",
    "the requested url returned error: 5",
    "the requested url returned error: 429",
    "early eof",
)


class CheckoutError(RuntimeError):
    """A git command failed, or the repo cannot be cloned at all.

    `transient` is set when the failure was ours or the network's, a
    timeout or a missing git, so the caller knows not to read it as a
    verdict on the repo.
    """

    def __init__(self, message: str, *, transient: bool = False):
        super().__init__(message)
        self.transient = transient


@dataclass
class ScanResult:
    """What one scan of one checkout found.

    Two kinds of count, from the same parse. ``usage`` is every symbol
    the source resolves to; ``patterns`` is django-probe's named probes,
    which answer questions a dotted path cannot, like whether
    ``transaction.atomic`` was used as a decorator or a context manager.
    """

    usage: Counter[str] = field(default_factory=Counter)
    patterns: Counter[str] = field(default_factory=Counter)
    # What the scan looked for, kept so a zero can be told apart from
    # never having asked. A profile with no rest_framework symbols means
    # nothing unless we know rest_framework was among the libraries.
    libraries: tuple[str, ...] = ()
    files_scanned: int = 0
    files_skipped: int = 0

    @property
    def symbols(self) -> int:
        return len(self.usage)

    @property
    def total(self) -> int:
        return sum(self.usage.values())

    @staticmethod
    def library_of(symbol: str) -> str:
        """The top-level import a symbol belongs to.

        ``django.db.models.CharField`` belongs to ``django``. Stored
        beside each symbol rather than worked out at read time, so
        grouping by library is a plain GROUP BY.
        """
        return symbol.partition(".")[0]

    @property
    def by_library(self) -> Counter[str]:
        """Uses per library, for when the question is which one at all."""
        totals: Counter[str] = Counter()
        for symbol, count in self.usage.items():
            totals[self.library_of(symbol)] += count
        return totals

    @property
    def settings_used(self) -> Counter[str]:
        """Named Django settings the source reads, without the prefix.

        A setting we do not recognise folds to a bare
        ``django.conf.settings`` in ``usage``, so this only ever reports
        real setting names.
        """
        return Counter(
            {
                symbol.removeprefix(SETTINGS_PREFIX): count
                for symbol, count in self.usage.items()
                if symbol.startswith(SETTINGS_PREFIX)
            }
        )


def is_cloneable(repo_url: str) -> bool:
    host = urlparse(repo_url or "").netloc.lower().removeprefix("www.")
    return host in CLONEABLE_HOSTS


def scannable_packages(*, min_score: int | None = 0):
    """The packages worth keeping a checkout of.

    A repo we can clone from and a PyPI release, because a package with
    no release is usually an abandoned idea or someone's fork, and its
    imports say nothing about what the ecosystem actually depends on.
    Narrowing here rather than at the call site keeps sync and scan
    looking at the same set, so a scan cannot quietly cover less than
    the sync fetched.

    The exception is a package tagged as an awesome list: no release and
    often no score to speak of, but its README is what we are after.
    """
    from package.models import Package, PackageTag

    host_q = Q()
    for host in CLONEABLE_HOSTS:
        host_q |= Q(repo_url__icontains=host)

    # A curated list (awesome-django and friends) is the one kind of repo
    # we keep without a PyPI release or a score: its README is the data.
    awesome_q = Q(tags__contains=[PackageTag.AWESOME_LIST])
    released_q = ~Q(pypi_url="")
    # A negative score is not a popularity judgement. The penalties only
    # overtake the stars after roughly thirty months without a commit, so
    # below zero reads as abandoned, whether the package has three stars
    # or three thousand. Zero is kept deliberately: a package added
    # yesterday has no stars and scores zero.
    if min_score is not None:
        released_q &= Q(score__gte=min_score)

    return (
        Package.objects.exclude(repo_url="")
        .filter(host_q)
        .filter(released_q | awesome_q)
        # probe is the stored verdict from check_package_sources: can we
        # clone it at all. probe_wanted is ours: do we want to. Null on
        # either means undecided, which we take as "worth a try", so a
        # new package does not wait to be approved one at a time.
        .exclude(probe=False)
        .exclude(probe_wanted=False)
        # Django itself is not one of the packages we probe. Its source
        # defines the symbols we count rather than using them, so it
        # would come out as the heaviest user of its own API and drown
        # every real package in the roll-ups.
        .exclude(
            Q(slug__iexact="django") | Q(repo_url__icontains="github.com/django/django")
        )
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
        raise CheckoutError(
            "git is not installed in this image", transient=True
        ) from exc
    except subprocess.TimeoutExpired as exc:
        raise CheckoutError(
            f"git {args[0]} timed out after {timeout}s", transient=True
        ) from exc

    if result.returncode != 0:
        output = (result.stderr or result.stdout).strip()
        detail = output.splitlines()
        lowered = output.lower()
        raise CheckoutError(
            detail[-1] if detail else f"git {args[0]} failed",
            transient=any(error in lowered for error in NETWORK_ERRORS),
        )

    return result.stdout


def repo_is_reachable(repo_url: str, *, timeout: int = 30) -> tuple[bool | None, str]:
    """Ask the remote whether it exists, without downloading it.

    `git ls-remote` is a single request that returns the ref list, so a
    dead or private repo costs a round trip instead of a clone. At four
    thousand packages that is the difference between a pre-flight check
    and an afternoon.

    Returns None instead of False when the check itself failed, a
    timeout or a dropped connection, since that is no answer at all.
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
        if exc.transient:
            return None, detail
        return False, detail
    return True, ""


def pypi_is_published(
    pypi_url: str, *, timeout: float = 10.0
) -> tuple[bool | None, str]:
    """Whether PyPI still serves this project.

    A package can be delisted or renamed long after we recorded it, and
    the stored pypi_url is not evidence that anything is there now.

    Returns None instead of False when PyPI could not answer, a network
    error or a 5xx or a rate limit, so a bad minute is not recorded as
    the project being gone.
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
        return None, f"pypi unreachable: {type(exc).__name__}"

    if response.status_code in (404, 410):
        return False, "not on pypi"
    if response.status_code == 429 or response.status_code >= 500:
        return None, f"pypi returned {response.status_code}"
    if response.status_code >= 400:
        return False, f"pypi returned {response.status_code}"
    return True, ""


def checkout_size(path: Path) -> int:
    """Bytes on disk under a checkout, .git and all.

    Walked rather than shelled out to `du`, so it works the same on the
    server and in a test, and counts what the filesystem reports rather
    than block usage.
    """
    total = 0
    for dirpath, _dirnames, filenames in os.walk(path):
        for name in filenames:
            try:
                total += (Path(dirpath) / name).lstat().st_size
            except OSError:
                # A file that vanished mid-walk, or a broken symlink.
                continue
    return total


def discard_checkout(path: Path) -> None:
    """Delete a checkout we have decided we do not want."""
    shutil.rmtree(path, ignore_errors=True)


def sync_checkout(package, *, depth: int = 1, timeout: int = 300) -> tuple[Path, str]:
    """Clone the package's repo, or bring an existing checkout up to date.

    Returns the path and what happened, "cloned" or "updated". Shallow by
    default: we only ever read the working tree, so history is weight we
    do not need across thousands of repos. A depth of 0 means full
    history, which git spells as no --depth at all.
    """
    depth_args = ("--depth", str(depth)) if depth > 0 else ()

    if not is_cloneable(package.repo_url):
        raise CheckoutError(f"cannot clone from {package.repo_url or 'no repo url'}")

    path = checkout_path(package)

    if (path / ".git").is_dir():
        # Reset rather than pull: the tree is ours to throw away, and a
        # merge conflict in a checkout nobody edits is not worth handling.
        #
        # HEAD rather than the default refspec, which names the branch we
        # cloned. A repo that renames master to main would otherwise
        # fail every fetch from then on.
        _git("fetch", *depth_args, "origin", "HEAD", cwd=path, timeout=timeout)
        head = _git("rev-parse", "FETCH_HEAD", cwd=path, timeout=timeout).strip()
        _git("reset", "--hard", head, cwd=path, timeout=timeout)
        _git("clean", "-qfdx", cwd=path, timeout=timeout)
        return path, "updated"

    path.parent.mkdir(parents=True, exist_ok=True)
    _git(
        "clone",
        *depth_args,
        "--quiet",
        package.repo_url,
        str(path),
        timeout=timeout,
    )
    return path, "cloned"


def iter_python_files(root: Path):
    """Every .py file in a checkout, leaving out symlinks.

    A symlink in somebody else's repo can point anywhere: at a file
    outside the checkout, or at /dev/zero, which would never finish
    reading. Either way it is not the package's own source.
    """
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [
            d for d in dirnames if d not in SKIP_DIRS and not d.endswith(".egg-info")
        ]
        for name in filenames:
            path = Path(dirpath) / name
            if name.endswith(".py") and not path.is_symlink():
                yield path


def checkout_commit(root: Path) -> str:
    """The commit the working tree is on, read straight off disk.

    Deliberately not `git rev-parse`: the scan runs over thousands of
    checkouts and shelling out once each would dominate it, for a value
    that is sitting in two small files. It also keeps the scan a pure
    filesystem reader, which is what lets it promise never to run git
    at all.

    Returns "" rather than raising, since a missing commit should
    degrade a profile, not fail a scan.
    """
    git_dir = root / ".git"
    try:
        head = (git_dir / "HEAD").read_text().strip()
    except OSError:
        return ""

    if not head.startswith("ref:"):
        # Detached, so HEAD already holds the sha.
        return head

    ref = head.removeprefix("ref:").strip()
    try:
        return (git_dir / ref).read_text().strip()
    except OSError:
        pass

    # A freshly cloned repo keeps its refs in packed-refs instead of as
    # loose files.
    try:
        for line in (git_dir / "packed-refs").read_text().splitlines():
            if line.startswith(("#", "^")):
                continue
            sha, _, name = line.partition(" ")
            if name.strip() == ref:
                return sha.strip()
    except OSError:
        pass

    return ""


def scan_checkout(root: Path, packages: tuple[str, ...] = ("django",)) -> ScanResult:
    """Count what a checkout uses, by symbol and by named pattern.

    The counting is django-probe's: a NodeVisitor that follows import
    aliasing, so ``from django.db import models`` and a later
    ``models.CharField`` resolve to the full dotted path rather than being
    matched as text.

    Setting names are handed over so that ``settings.AUTH_USER_MODEL``
    stays distinct instead of folding into a bare ``django.conf.settings``
    along with every other setting in the file.
    """
    # Importing the probes package is what registers the probes; without
    # it count_patterns has nothing to count and returns an empty tally.
    import django_probe.probes  # noqa: F401
    from django_probe.ast_probe import count_patterns
    from django_probe.settings import DJANGO_SETTING_NAMES
    from django_probe.usage import count_package_usage

    result = ScanResult(libraries=tuple(packages))

    for path in iter_python_files(root):
        # Some probes key off the filename, so they need the path within
        # the checkout. It never leaves this function.
        relative = str(path.relative_to(root))
        try:
            if path.stat().st_size > MAX_FILE_BYTES:
                result.files_skipped += 1
                continue
            # Parsed as bytes, not text. A file that opens with a UTF-8
            # BOM keeps it as U+FEFF when decoded, which the parser
            # rejects as a non-printable character, and a file declaring
            # a non-UTF-8 coding has to be decoded by the parser to be
            # read at all. Both are common in packages this old.
            with warnings.catch_warnings():
                # A decade-old repo is full of invalid escape sequences.
                # Nobody can act on the warning, so it should not reach
                # the output of a scan over four thousand of them.
                warnings.simplefilter("ignore")
                tree = ast.parse(path.read_bytes())
            usage = count_package_usage(tree, packages, DJANGO_SETTING_NAMES)
            patterns = count_patterns(tree, relative)
        except (
            OSError,
            UnicodeDecodeError,
            SyntaxError,
            ValueError,
            # A deeply nested expression overflows the parser, which says
            # so with a MemoryError, or the visitor, with a RecursionError.
            MemoryError,
            RecursionError,
        ):
            # Other people's repos hold unparseable and non-UTF-8 files.
            # One bad file should not fail the package, let alone the run.
            result.files_skipped += 1
            continue

        result.usage.update(usage)
        result.patterns.update(patterns)
        result.files_scanned += 1

    return result
