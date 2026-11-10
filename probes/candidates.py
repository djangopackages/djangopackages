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
from django.db.models import F, Q
from django.utils import timezone

from package.importer import repo_url_from_pypi
from package.models import Package
from package.pypi import PyPIClient, PyPIPackage
from probes.discovery import Discovery
from probes.ecosystems import BULK_SIZE, EcosystemsClient, canonical
from probes.models import Candidate

logger = logging.getLogger(__name__)

# Requests to leave in ecosyste.ms's daily quota for everything else.
ECOSYSTEMS_RESERVE = 500

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


def record(found: Discovery) -> Recorded:
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
                "classifiers": list(row.classifiers),
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
    """Fetch the PyPI JSON for one candidate, and its ecosyste.ms record
    too when an `ecosystems` client is passed.

    Returns False when PyPI had nothing for the name or the request
    failed. A 404 stamps `pypi_fetched_at` with no data, which is how a
    removed project is told apart; any other failure leaves the row as
    it was so the next run tries again. The ecosyste.ms half is best
    effort and never blocks the PyPI half. `enrich_missing` leaves it
    out and asks ecosyste.ms in batches of 100 instead.
    """
    client = client or PyPIClient()
    try:
        pypi = client.fetch_package(candidate.name)
    except httpx2.HTTPStatusError as exc:
        status = exc.response.status_code if exc.response is not None else "?"
        logger.info("PyPI returned %s for candidate %s", status, candidate.name)
        if status == 404:
            # Deleted by its author or removed by PyPI; BigQuery keeps the
            # uploads either way. Stamp it so screening can say so and the
            # next run does not ask again unless a newer upload appears.
            candidate.pypi_fetched_at = timezone.now()
            candidate.save(update_fields=["pypi_fetched_at", "modified"])
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

    if ecosystems is not None:
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

    apply_ecosystems(candidate, record)
    if save:
        candidate.save()
    return record is not None


def apply_ecosystems(candidate: Candidate, record: dict | None) -> None:
    """Store a record, or a miss: they lag PyPI by days for new names, so
    a miss is the timestamp alone and the row is asked about again later.
    The repository fills in only when PyPI named none."""
    candidate.ecosystems_fetched_at = timezone.now()
    if record is None:
        candidate.ecosystems_data = {}
        return
    candidate.ecosystems_data = record
    if not candidate.repo_url and record.get("repository_url"):
        candidate.repo_url = record["repository_url"][:500]


@dataclass
class Enriched:
    pypi: int = 0
    ecosystems_asked: int = 0
    ecosystems_found: int = 0
    ecosystems_requests: int = 0
    ecosystems_remaining: int | None = None
    stopped_early: bool = False


def enrich_missing(
    *,
    limit: int | None = None,
    ecosystems_limit: int | None = None,
    client: PyPIClient | None = None,
    ecosystems: EcosystemsClient | None = None,
) -> Enriched:
    """Fill in candidates in two passes.

    PyPI first: every row with no PyPI data yet, newest first, capped by
    `limit`. Names PyPI already answered 404 for are skipped unless
    BigQuery has seen an upload since we asked.

    Then ecosyste.ms, 100 names a request, for every row with PyPI data
    and no record from them, never asked first and then oldest attempt,
    capped by `ecosystems_limit` names. It stops early on an error or
    when their quota header drops below `ECOSYSTEMS_RESERVE`, so a big
    backlog spreads itself over a few runs on its own.
    """
    client = client or PyPIClient()
    ecosystems = ecosystems or EcosystemsClient()
    result = Enriched()

    rows = (
        Candidate.objects.filter(pypi_data={})
        .filter(
            Q(pypi_fetched_at__isnull=True) | Q(last_upload__gt=F("pypi_fetched_at"))
        )
        .order_by("-last_upload", "name")
    )
    if limit is not None:
        rows = rows[:limit]
    for candidate in rows:
        if enrich(candidate, client=client):
            result.pypi += 1

    pending = (
        Candidate.objects.exclude(pypi_data={})
        .filter(ecosystems_data={})
        .exclude(status__in=[Candidate.Status.REJECTED, Candidate.Status.IMPORTED])
        .order_by(F("ecosystems_fetched_at").asc(nulls_first=True), "name")
    )
    if ecosystems_limit is not None:
        pending = pending[:ecosystems_limit]
    batch: list[Candidate] = []
    for candidate in pending.iterator(chunk_size=BULK_SIZE):
        batch.append(candidate)
        if len(batch) == BULK_SIZE:
            if not _ecosystems_batch(batch, ecosystems, result):
                break
            batch = []
    else:
        if batch:
            _ecosystems_batch(batch, ecosystems, result)
    result.ecosystems_requests = ecosystems.requests
    result.ecosystems_remaining = ecosystems.remaining
    return result


def _ecosystems_batch(
    batch: list[Candidate], ecosystems: EcosystemsClient, result: Enriched
) -> bool:
    """One bulk request. False means stop asking for this run."""
    if ecosystems.remaining is not None and ecosystems.remaining < ECOSYSTEMS_RESERVE:
        logger.warning("ecosyste.ms quota down to %s; stopping", ecosystems.remaining)
        result.stopped_early = True
        return False
    try:
        found = ecosystems.fetch_packages(c.name for c in batch)
    except httpx2.HTTPError as exc:
        logger.warning("ecosyste.ms bulk lookup failed: %s", exc)
        result.stopped_early = True
        return False
    now = timezone.now()
    for candidate in batch:
        apply_ecosystems(candidate, found.get(canonical(candidate.name)))
        candidate.modified = now
    Candidate.objects.bulk_update(
        batch, ["ecosystems_data", "ecosystems_fetched_at", "repo_url", "modified"]
    )
    result.ecosystems_asked += len(batch)
    result.ecosystems_found += len(found)
    return True


def mark_imported(name: str, package: Package) -> None:
    """Called by the importer so a candidate row follows its package."""
    Candidate.objects.filter(name__iexact=name).update(
        status=Candidate.Status.IMPORTED, package=package, modified=timezone.now()
    )
