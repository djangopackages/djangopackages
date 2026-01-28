from __future__ import annotations

from typing import TYPE_CHECKING

from django.db import models
from looseversion import LooseVersion
from requests.compat import quote
from trove_classifiers import classifiers

if TYPE_CHECKING:
    from django.db.models import QuerySet


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


def get_version(package):
    # Prefer prefetched versions when available to avoid N+1 queries.
    prefetched = getattr(package, "_prefetched_versions", None)

    if prefetched:
        return prefetched[0]

    versions = package.version_set.exclude(upload_time=None)
    try:
        return versions.latest()
    except models.ObjectDoesNotExist:
        return None


def get_pypi_version(package):
    # Prefer prefetched versions when available to avoid N+1 queries.
    prefetched = getattr(package, "_prefetched_versions", None)

    if prefetched is not None:
        numbers = [v.number for v in prefetched]
    else:
        numbers = package.version_set.values_list("number", flat=True)

    versions = []
    for v_str in numbers:
        v = LooseVersion(v_str)
        comparable = True
        for elem in v.version:
            if isinstance(elem, str):
                comparable = False
        if comparable:
            versions.append(v)
    if versions:
        return str(sorted(versions)[-1])
    return ""


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
