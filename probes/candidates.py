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
from probes.ecosystems import EcosystemsClient
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


def enrich(
    candidate: Candidate,
    *,
    client: PyPIClient | None = None,
    ecosystems: EcosystemsClient | None = None,
) -> bool:
    """Fetch the PyPI JSON and the ecosyste.ms record for one candidate.

    Returns False when PyPI had nothing for the name or the request
    failed; the row is left as it was so the next run tries again. The
    ecosyste.ms half is best effort: they lag PyPI by days for new
    names, so a miss is recorded by the timestamp alone and retried
    later, and an outage there never blocks the PyPI half.
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

    enrich_from_ecosystems(candidate, ecosystems=ecosystems, save=False)
    candidate.save()
    return True


def enrich_from_ecosystems(
    candidate: Candidate,
    *,
    ecosystems: EcosystemsClient | None = None,
    save: bool = True,
) -> bool:
    """Store what ecosyste.ms knows; fill the repository if PyPI gave none."""
    ecosystems = ecosystems or EcosystemsClient()
    try:
        record = ecosystems.fetch_package(candidate.name)
    except httpx2.HTTPError as exc:
        logger.warning("ecosyste.ms failed for candidate %s: %s", candidate.name, exc)
        return False

    candidate.ecosystems_fetched_at = timezone.now()
    if record is None:
        candidate.ecosystems_data = {}
    else:
        candidate.ecosystems_data = record
        if not candidate.repo_url and record.get("repository_url"):
            candidate.repo_url = record["repository_url"][:500]
    if save:
        candidate.save()
    return record is not None


def enrich_missing(
    *,
    limit: int | None = None,
    client: PyPIClient | None = None,
    ecosystems: EcosystemsClient | None = None,
) -> int:
    """Fill in every candidate that has no PyPI data yet, newest first.

    Then retry ecosyste.ms for rows it did not know last time, oldest
    attempt first, within the same cap, since their index catches up
    with PyPI over a few days.
    """
    client = client or PyPIClient()
    ecosystems = ecosystems or EcosystemsClient()
    rows = Candidate.objects.filter(pypi_data={}).order_by("-last_upload", "name")
    if limit is not None:
        rows = rows[:limit]
    done = 0
    for candidate in rows:
        if enrich(candidate, client=client, ecosystems=ecosystems):
            done += 1

    retry = (
        Candidate.objects.exclude(pypi_data={})
        .filter(ecosystems_data={})
        .exclude(status__in=[Candidate.Status.REJECTED, Candidate.Status.IMPORTED])
        .order_by("ecosystems_fetched_at", "name")
    )
    if limit is not None:
        retry = retry[: max(limit - done, 0)]
    for candidate in retry:
        enrich_from_ecosystems(candidate, ecosystems=ecosystems)
    return done


def mark_imported(name: str, package: Package) -> None:
    """Called by the importer so a candidate row follows its package."""
    Candidate.objects.filter(name__iexact=name).update(
        status=Candidate.Status.IMPORTED, package=package, modified=timezone.now()
    )
