"""The probe pipeline as Django Q tasks.

The expensive steps, asking whether a repo still answers and fetching
its checkout, are independent per package and network bound, so they
run one package per task and the cluster fans them out. The single
pass steps, `build_probe_profiles` and `build_probe_catalog`, stay as
scheduled management commands; see `init_scheduled_jobs`.

Scanning rides along with the sync: the checkout is on disk and the
profile skips a commit it has already read, so a separate scan task
would only add a queue round trip.
"""

from __future__ import annotations

from datetime import timedelta

from django.db.models import Q
from django.utils.timezone import now
from django_q.tasks import async_task

from package.models import Package
from probes import pipeline
from probes.checkouts import is_cloneable, scannable_packages

# How long a verdict from check_source stands before it is asked again.
# A repo that was private last month may be public today, and one that
# answered last month may be gone.
STALE_AFTER_DAYS = 30

# Per task. A sync waits up to 300s on git, then reads the tree; the
# cluster default of 600s would cut the largest checkouts short.
REFRESH_TIMEOUT = 20 * 60


def check_package_source(slug: str, *, timeout: int = 30) -> str:
    """Record whether one package's repo and PyPI project still answer."""
    package = Package.objects.select_related("latest_version").get(slug=slug)
    ok, note = pipeline.check_source(package, timeout=timeout)
    if ok is None:
        return f"no answer: {note}"
    return "on" if ok else f"off: {note}"


def refresh_package_checkout(
    slug: str,
    *,
    depth: int = 1,
    timeout: int = 300,
    max_mb: int | None = None,
    force: bool = False,
) -> str:
    """Sync one checkout, record its import names, and scan it."""
    package = Package.objects.select_related("probe_profile").get(slug=slug)

    if not is_cloneable(package.repo_url):
        return f"skipped: cannot clone from {package.repo_url or 'no repo url'}"

    outcome = pipeline.sync_package(
        package, depth=depth, timeout=timeout, max_mb=max_mb
    )
    if not outcome.ok:
        return f"{outcome.action}: {outcome.note}"

    pipeline.record_import_names(package)
    status, _result = pipeline.scan_package(package, force=force)
    return f"{outcome.action}, {status}"


def queue_probe_refresh(
    *,
    stale_after_days: int = STALE_AFTER_DAYS,
    min_score: int = 0,
    max_mb: int | None = None,
    limit: int | None = None,
) -> dict[str, int]:
    """Fan the pipeline out: one task per package for each expensive step.

    Meant to run from a schedule. Source checks go to packages nobody
    has decided on yet and to decided ones whose verdict has gone stale.
    Checkout refreshes go to everything `scannable_packages` returns,
    which is the same set the commands use.
    """
    cutoff = now() - timedelta(days=stale_after_days)
    to_check = (
        Package.objects.exclude(repo_url="")
        .filter(
            Q(probe__isnull=True)
            | Q(probe_checked_at__isnull=True)
            | Q(probe_checked_at__lt=cutoff)
        )
        .order_by("-score", "title")
        .values_list("slug", flat=True)
    )
    to_refresh = scannable_packages(min_score=min_score).values_list("slug", flat=True)
    if limit:
        to_check = to_check[:limit]
        to_refresh = to_refresh[:limit]

    checks = 0
    for slug in to_check.iterator():
        async_task(
            "probes.tasks.check_package_source",
            slug,
            q_options={"group": "probe-check", "task_name": f"probe-check:{slug}"},
        )
        checks += 1

    refreshes = 0
    for slug in to_refresh.iterator():
        async_task(
            "probes.tasks.refresh_package_checkout",
            slug,
            max_mb=max_mb,
            q_options={
                "group": "probe-refresh",
                "task_name": f"probe-refresh:{slug}",
                "timeout": REFRESH_TIMEOUT,
            },
        )
        refreshes += 1

    return {"checks": checks, "refreshes": refreshes}
