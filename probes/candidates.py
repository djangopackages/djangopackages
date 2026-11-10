"""Turn discovery rows into candidate rows, and fill them in from PyPI.

Two steps, kept apart because they cost different things. `record` is a
handful of upserts from a query we already ran. `enrich` is one HTTP
request per candidate to PyPI, so it is run for the rows that have no
data yet and can be capped.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

import httpx2
from django.utils import timezone

from package.importer import repo_url_from_pypi
from package.models import Package
from package.pypi import PyPIClient, PyPIPackage
from probes.discovery import Discovery
from probes.models import Candidate

logger = logging.getLogger(__name__)

# Keys of the PyPI `info` block worth keeping. `description` is the
# whole README and can run to hundreds of kilobytes; everything else is
# small and is what the rules and the admin read.
INFO_KEYS = (
    "name",
    "version",
    "summary",
    "author",
    "author_email",
    "maintainer",
    "maintainer_email",
    "license",
    "home_page",
    "project_urls",
    "requires_dist",
    "requires_python",
    "classifiers",
    "keywords",
    "yanked",
)


@dataclass
class Recorded:
    created: int = 0
    refreshed: int = 0
    linked: int = 0  # already indexed names that had a stale candidate row
    names: list[str] = field(default_factory=list)


def record(found: Discovery, framework: str) -> Recorded:
    """Upsert one candidate per new name; refresh the ones seen before.

    A row's status is never touched here. Rejected stays rejected,
    whatever the next run says about the name. Names discovery reports
    as already indexed only matter when a candidate row exists for
    them, in which case it is marked imported and linked.
    """
    now = timezone.now()
    result = Recorded()
    for row in found.new:
        candidate, created = Candidate.objects.update_or_create(
            name=row.name,
            defaults={
                "framework": framework,
                "version": row.version,
                "summary": row.summary,
                "home_page": row.home_page[:500],
                "first_upload": row.first_upload,
                "last_upload": row.last_upload,
                "last_seen": now,
            },
        )
        result.names.append(candidate.name)
        if created:
            result.created += 1
        else:
            result.refreshed += 1

    tracked = {row.name: pk for row, pk in found.tracked}
    if tracked:
        stale = Candidate.objects.filter(name__in=tracked).exclude(
            status=Candidate.Status.IMPORTED
        )
        for candidate in stale:
            candidate.status = Candidate.Status.IMPORTED
            candidate.package_id = tracked[candidate.name]
            candidate.save(update_fields=["status", "package", "modified"])
            result.linked += 1
    return result


def trimmed(pypi: PyPIPackage) -> dict:
    """The parts of the PyPI JSON a candidate keeps."""
    info = {key: pypi.info.get(key) for key in INFO_KEYS if key in pypi.info}
    releases = {}
    for version, files in (pypi.raw.get("releases") or {}).items():
        dates = [f.get("upload_time_iso_8601") or f.get("upload_time") for f in files]
        dates = [d for d in dates if d]
        if dates:
            releases[version] = min(dates)
    return {"info": info, "releases": releases}


def enrich(candidate: Candidate, *, client: PyPIClient | None = None) -> bool:
    """Fetch the PyPI JSON for one candidate and store what matters.

    Returns False when PyPI had nothing for the name or the request
    failed; the row is left as it was so the next run tries again.
    """
    client = client or PyPIClient()
    try:
        pypi = client.fetch_package(candidate.name)
    except httpx2.HTTPStatusError as exc:
        status = exc.response.status_code if exc.response is not None else "?"
        logger.info("PyPI returned %s for candidate %s", status, candidate.name)
        return False
    except httpx2.RequestError as exc:
        logger.warning("PyPI request failed for candidate %s: %s", candidate.name, exc)
        return False

    candidate.pypi_data = trimmed(pypi)
    candidate.pypi_fetched_at = timezone.now()
    candidate.repo_url = repo_url_from_pypi(pypi) or ""
    if pypi.version:
        candidate.version = pypi.version
    if pypi.info.get("summary"):
        candidate.summary = pypi.info["summary"]
    candidate.save()
    return True


def enrich_missing(
    *, limit: int | None = None, client: PyPIClient | None = None
) -> int:
    """Fill in every candidate that has no PyPI data yet, newest first."""
    rows = Candidate.objects.filter(pypi_data={}).order_by("-last_upload", "name")
    if limit is not None:
        rows = rows[:limit]
    client = client or PyPIClient()
    done = 0
    for candidate in rows:
        if enrich(candidate, client=client):
            done += 1
    return done


def mark_imported(name: str, package: Package) -> None:
    """Called by the importer so a candidate row follows its package."""
    Candidate.objects.filter(name__iexact=name).update(
        status=Candidate.Status.IMPORTED, package=package, modified=timezone.now()
    )
