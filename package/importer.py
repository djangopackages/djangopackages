"""Create a package from its PyPI project, then fill it in.

The discovery feed (`pypi_discover`, #1810) produces names. This turns a
name into a `Package` the way a person would through the add form: a
title, a slug, the PyPI URL and the repository URL, in a category. Then
it runs the same fetches the site runs for any package, PyPI metadata,
repository metadata and the score, so the new row is as complete as an
existing one.

A repository URL is required. `Package.repo_url` is unique, so two
packages without one would collide, and a package with no repository
has nothing for the probes or the score to read. A project whose PyPI
links name no forge is reported, not created.

Nothing here decides whether a project belongs on the site. That is
the review step before this runs, and the spam and malware filter that
has to exist before it is ever scheduled.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from urllib.parse import urlparse

import httpx2
from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify

from package.models import Category, Package, PackageTag
from package.pypi import PyPIClient, PyPIPackage, update_package_from_pypi
from package.repos.repo_url_normelizer import normalize_repo_url
from package.scores import update_package_score
from probes.awesome import package_index, repo_key
from probes.imports import canonical_name

logger = logging.getLogger(__name__)

# Project URL labels that name the source, most specific first. Checked
# before the generic hostname test so "Homepage: github.com/x/docs-site"
# does not beat "Source: github.com/x/package".
_SOURCE_LABELS = (
    "source",
    "source code",
    "sourcecode",
    "code",
    "repository",
    "repo",
    "github",
    "gitlab",
    "codeberg",
    "bitbucket",
    "homepage",
    "home",
)

# Hosts where two path segments name a repository.
_FORGE_HOSTS = {"github.com", "gitlab.com", "bitbucket.org", "codeberg.org"}


@dataclass
class ImportResult:
    name: str
    status: str  # created | exists | no_repo | not_on_pypi | error | dry_run
    package: Package | None = None
    note: str = ""

    @property
    def created(self) -> bool:
        return self.status == "created"


def repo_url_from_pypi(pypi_info: PyPIPackage) -> str | None:
    """The first project link that points at a repository on a forge.

    Labels are tried in `_SOURCE_LABELS` order, then any link at all on a
    forge host, since authors file the repo under "Bug Tracker" or
    "Download" often enough. Returned normalised, or None.
    """
    links = {
        str(label).strip().lower(): str(url).strip()
        for label, url in pypi_info.project_urls.items()
        if label and url
    }
    ordered = [links[label] for label in _SOURCE_LABELS if label in links]
    ordered += [url for label, url in links.items() if label not in _SOURCE_LABELS]
    for url in ordered:
        if _looks_like_repo(url):
            try:
                return normalize_repo_url(url)
            except Exception:  # noqa: BLE001  the normaliser raises plain ValueError-likes
                continue
    return None


def _looks_like_repo(url: str) -> bool:
    parsed = urlparse(url)
    host = (parsed.netloc or "").lower().removeprefix("www.")
    if host not in _FORGE_HOSTS:
        return False
    parts = [p for p in parsed.path.split("/") if p]
    # owner/repo, with nothing after it that is not a tree or blob view
    # (issue and wiki pages are on the repo but are not the repo).
    return len(parts) >= 2 and (len(parts) == 2 or parts[2] in {"tree", "blob"})


def unique_slug(name: str) -> str:
    base = slugify(name)[:40] or "package"
    slug = base
    suffix = 2
    while Package.objects.filter(slug=slug).exists():
        slug = f"{base}-{suffix}"
        suffix += 1
    return slug


def import_from_pypi(
    name: str,
    *,
    category: Category,
    client: PyPIClient | None = None,
    dry_run: bool = False,
    index: tuple[dict, dict] | None = None,
) -> ImportResult:
    """Create one package from its PyPI name and fill it in.

    `index` is the `(by_repo, by_pypi)` pair from `package_index()`;
    pass it in when importing a list so the catalogue is read once.
    """
    canonical = canonical_name(name)
    by_repo, by_pypi = index or package_index()
    if pk := by_pypi.get(canonical):
        return ImportResult(
            name, "exists", Package.objects.get(pk=pk), "same PyPI name"
        )

    client = client or PyPIClient()
    try:
        pypi_info = client.fetch_package(canonical)
    except httpx2.HTTPStatusError as exc:
        status = exc.response.status_code if exc.response is not None else None
        if status == 404:
            return ImportResult(name, "not_on_pypi")
        return ImportResult(name, "error", note=f"PyPI returned {status}")
    except httpx2.RequestError as exc:
        return ImportResult(name, "error", note=f"PyPI request failed: {exc}")

    repo_url = repo_url_from_pypi(pypi_info)
    if not repo_url:
        return ImportResult(name, "no_repo", note="no repository link on PyPI")
    if (key := repo_key(repo_url)) and (pk := by_repo.get(key)):
        return ImportResult(
            name, "exists", Package.objects.get(pk=pk), f"same repository {repo_url}"
        )
    if Package.objects.filter(repo_url=repo_url).exists():
        return ImportResult(
            name, "exists", Package.objects.get(repo_url=repo_url), "same repository"
        )

    if dry_run:
        return ImportResult(name, "dry_run", note=f"would create with {repo_url}")

    with transaction.atomic():
        package = Package.objects.create(
            title=pypi_info.name or canonical,
            slug=unique_slug(pypi_info.name or canonical),
            pypi_url=f"https://pypi.org/project/{pypi_info.name or canonical}/",
            repo_url=repo_url,
            category=category,
            tags=[PackageTag.PYPI_IMPORT],
        )
    fill_in(package, client=client)
    mark_imported(name, package)
    # Keep the index current for the rest of a batch run.
    by_pypi[canonical] = package.pk
    if key:
        by_repo[key] = package.pk
    return ImportResult(name, "created", package)


def mark_imported(name: str, package: Package) -> None:
    """Let the candidate row, if there is one, follow its package.

    Imported inside the function: probes.candidates imports this module
    for repo_url_from_pypi, and a module-level import would be circular.
    """
    from probes.candidates import mark_imported as _mark

    _mark(name, package)


def fill_in(package: Package, *, client: PyPIClient | None = None) -> Package:
    """The same fetches `fetch_package_data_task` runs, tolerating a repo
    host that is down: a package with PyPI data and no stars is still a
    package, and the package updater will try the repo again."""
    update_package_from_pypi(package, client=client, save=False)
    try:
        package.repo.fetch_metadata(package, save=False)
    except Exception:  # noqa: BLE001
        logger.exception("Repository metadata failed for %s", package.slug)
    update_package_score(package, save=False)
    package.last_fetched = timezone.now()
    package.save()
    return package
