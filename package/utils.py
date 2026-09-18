from __future__ import annotations

from typing import TYPE_CHECKING
from urllib.parse import quote, urlparse

from trove_classifiers import classifiers

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

    Homepages that point at the package's own repository or at PyPI are skipped.
    """
    if not url or not str(url).strip():
        return None

    candidate = str(url).strip()
    parsed = urlparse(candidate)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return None

    if parsed.netloc.lower() in _PYPI_NETLOCS:
        return None

    if repo_url and _normalized_url_key(candidate) == _normalized_url_key(repo_url):
        return None

    return candidate


def maybe_set_documentation_url(package: Package, url: str | None) -> bool:
    """Fill a blank documentation_url from a usable homepage URL.

    Returns True when the package field was updated.
    """
    if package.documentation_url:
        return False

    usable = usable_homepage_url(url, repo_url=package.repo_url)
    if not usable:
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


def normalize_license(license: str):
    """Handles when:

    * No license is passed
    * Made up licenses are submitted
    * Official PyPI trove classifier licenses
    * Common abbreviations of licenses

    """
    if license is not None:
        stripped_license = license.strip()
        if stripped_license.startswith("License") and stripped_license in classifiers:
            return stripped_license
        if len(stripped_license) > 20:
            return "Custom"
        return stripped_license
    return "UNKNOWN"


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
