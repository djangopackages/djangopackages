from __future__ import annotations

import re
from typing import TYPE_CHECKING
from urllib.parse import quote, urlparse


if TYPE_CHECKING:
    from django.db.models import QuerySet

    from package.models import Package

_PYPI_NETLOCS = frozenset(
    {
        "pypi.org",
        "www.pypi.org",
        "pypi.python.org",
        "www.pypi.python.org",
        "test.pypi.org",
        "www.test.pypi.org",
    }
)


def _normalized_url_key(url: str) -> str:
    parsed = urlparse(url.strip())
    netloc = parsed.netloc.lower()
    if netloc.startswith("www."):
        netloc = netloc[4:]
    path = parsed.path.rstrip("/").lower()
    if path.endswith(".git"):
        path = path[:-4]
    return f"{netloc}{path}"


def usable_homepage_url(url: str | None, *, repo_url: str | None = None) -> str | None:
    """Return a homepage URL that can stand in for documentation, or None.

    Homepages that point at the package's own repository, at any
    repository's README or bare page, or at PyPI are skipped: this is
    what the GitHub, Forgejo and PyPI updaters fill a blank documentation
    URL from, and a scan must not write back what the forms reject.
    """
    if not url or not str(url).strip():
        return None

    candidate = str(url).strip()
    parsed = urlparse(candidate)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return None

    if parsed.netloc.lower() in _PYPI_NETLOCS:
        return None

    if repo_url:
        repo_key = _normalized_url_key(repo_url)
        candidate_key = _normalized_url_key(candidate)
        if candidate_key == repo_key or candidate_key.startswith(f"{repo_key}/"):
            return None

    # A README or a bare owner/repo page elsewhere is no more
    # documentation than the package's own repository page is.
    if documentation_url_problem(candidate, repo_url=repo_url):
        return None

    return candidate


# Hosts where "owner/repo" with nothing after it is a repository page,
# which shows the README and nothing else.
_FORGE_NETLOCS = frozenset(
    {"github.com", "gitlab.com", "bitbucket.org", "codeberg.org", "sr.ht"}
)

# A README, however it is reached: "/blob/main/README.md", "/-/blob/main/README",
# "/src/master/README.rst", "/raw/main/README.txt".
_README_PATH = re.compile(r"/readme(\.[a-z0-9]+)?$", re.IGNORECASE)


def documentation_url_problem(url: str | None, *, repo_url: str | None = None) -> str:
    """Why a documentation URL is not documentation, or "" if it is fine.

    The documentation link exists to take a reader somewhere the
    repository page does not. A link back to the repository, to its
    README, or to the PyPI page is a link to something the package page
    already shows, so each is treated as having no documentation. A wiki
    or a docs folder inside the repository still counts: that is a
    separate thing to read.

        "pypi"   a pypi.org page
        "repo"   the package's own repository, with or without a fragment
        "readme" a README file in any repository
        "forge"  a bare owner/repo page on a code host (a moved or
                 re-cased copy of the repository link, nearly always)
    """
    if not url or not str(url).strip():
        return ""
    candidate = str(url).strip()
    parsed = urlparse(candidate)
    netloc = parsed.netloc.lower()
    if netloc.startswith("www."):
        netloc = netloc[4:]

    if netloc in _PYPI_NETLOCS:
        return "pypi"

    key = _normalized_url_key(candidate)
    if repo_url and key == _normalized_url_key(repo_url):
        return "repo"

    if _README_PATH.search(parsed.path.rstrip("/")):
        return "readme"

    if netloc in _FORGE_NETLOCS:
        segments = [s for s in parsed.path.split("/") if s]
        if segments and segments[-1].endswith(".git"):
            segments[-1] = segments[-1][:-4]
        # "owner/repo", or "~owner/repo" on sourcehut.
        if len(segments) == 2:
            return "forge"

    return ""


def usable_documentation_url(url: str | None, *, repo_url: str | None = None) -> str:
    """The URL if it points at documentation, else ""."""
    if not url or not str(url).strip():
        return ""
    if documentation_url_problem(url, repo_url=repo_url):
        return ""
    return str(url).strip()


def maybe_set_documentation_url(package: Package, url: str | None) -> bool:
    """Fill a blank documentation_url from a usable homepage URL.

    Returns True when the package field was updated.
    """
    if package.documentation_url:
        return False

    usable = usable_homepage_url(url, repo_url=package.repo_url)
    if not usable:
        return False

    max_length = package._meta.get_field("documentation_url").max_length
    if max_length and len(usable) > max_length:
        return False

    package.documentation_url = usable
    return True


# this is gross, but requests doesn't import quote_plus into compat,
# so we re-implement it here
def quote_plus(s, safe=""):
    """Quote the query fragment of a URL; replacing ' ' with '+'"""
    if " " in s:
        s = quote(s, f"{safe} ")
        return s.replace(" ", "+")
    return quote(s, safe)


def uniquer(seq, idfun=None):
    if idfun is None:

        def idfun(x):
            return x

    seen = {}
    result = []
    for item in seq:
        marker = idfun(item)
        if marker in seen:
            continue
        seen[marker] = 1
        result.append(item)
    return result


def normalize_license(license: str | None) -> str:
    """One spelling for a license, or UNKNOWN. See `package.licenses`."""
    from package import licenses

    return licenses.normalize(license) or licenses.UNKNOWN


def iterate_in_batches(queryset: QuerySet, batch_size: int):
    """
    Memory-efficient batch iteration over queryset.

    Iterates through a queryset in batches, yielding lists of primary keys.
    Uses values_list and iterator() to minimize memory footprint.

    Args:
        queryset: QuerySet to iterate
        batch_size: Size of each batch (must be >= 1)

    Yields:
        Lists of primary keys

    Example:
        >>> packages = Package.objects.filter(active=True)
        >>> for batch_pks in iterate_in_batches(packages, 500):
        ...     process_batch(batch_pks)
    """
    if batch_size < 1:
        raise ValueError("batch_size must be at least 1")

    pk_iterator = (
        queryset.order_by("pk")
        .values_list("pk", flat=True)
        .iterator(chunk_size=batch_size)
    )

    batch = []
    for pk in pk_iterator:
        batch.append(pk)
        if len(batch) >= batch_size:
            yield batch
            batch = []

    if batch:
        yield batch
