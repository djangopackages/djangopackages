from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Literal

from django.db.models import OuterRef, Subquery, Value, BooleanField, Max, QuerySet
from django.db.models.functions import Coalesce
from django.utils import timezone

from package.models import Commit, Package, Version
from package.utils import iterate_in_batches


@dataclass(frozen=True)
class CommitStats:
    """Aggregated commit statistics for packages."""

    last_commit_date: dict[int, timezone.datetime | None]
    weekly_histogram: dict[int, list[int]]


@dataclass(frozen=True)
class UpdateResult:
    """Result of an update operation."""

    updated_count: int
    total_count: int
    skipped_count: int = 0

    @property
    def success_rate(self) -> float:
        """Calculate the percentage of successfully updated items."""
        return (
            (self.updated_count / self.total_count * 100)
            if self.total_count > 0
            else 0.0
        )


def _aggregate_commit_stats(package_ids: list[int]) -> CommitStats:
    """
    Aggregate commit statistics for a batch of packages.

    Computes:
    1. Last commit date per package (max commit_date)
    2. 52-week histogram of commits per package

    Args:
        package_ids: Package IDs to process

    Returns:
        CommitStats with aggregated data
    """
    if not package_ids:
        return CommitStats(last_commit_date={}, weekly_histogram={})

    now = timezone.now()
    cutoff = now - timedelta(weeks=52)

    # Single query for last commit dates using aggregation
    last_dates = dict(
        Commit.objects.filter(package_id__in=package_ids)
        .values("package_id")
        .annotate(max_date=Max("commit_date"))
        .values_list("package_id", "max_date")
    )

    # Stream recent commits for histogram - only load what we need
    histogram_data: dict[int, list[int]] = {}

    for package_id, commit_date in (
        Commit.objects.filter(
            package_id__in=package_ids,
            commit_date__gte=cutoff,
            commit_date__lte=now,
            commit_date__isnull=False,
        )
        .values_list("package_id", "commit_date")
        .iterator(chunk_size=2000)
    ):
        age_weeks = (now - commit_date).days // 7

        # Only process valid weeks (0-51)
        if 0 <= age_weeks < 52:
            if package_id not in histogram_data:
                histogram_data[package_id] = [0] * 52
            histogram_data[package_id][age_weeks] += 1

    # Reverse for storage (oldest to newest)
    weekly_histogram = {
        pkg_id: list(reversed(weeks)) for pkg_id, weeks in histogram_data.items()
    }

    return CommitStats(last_commit_date=last_dates, weekly_histogram=weekly_histogram)


def _batch_update_versions(package_ids: list[int]) -> int:
    """
    Update latest_version and supports_python3 for a batch of packages using a single query.

    defaults supports_python3 to True if the version data is missing or Null.
    """
    if not package_ids:
        return 0

    # 1. Define the base subquery once to ensure consistency in ordering
    # Ensure you have a composite index on Version(package, hidden, upload_time)
    # for this to be truly efficient.
    latest_version_base = Version.objects.filter(
        package_id=OuterRef("pk"), hidden=False
    ).order_by("-upload_time", "-created", "-pk")

    # 2. Execute a single UPDATE query with two sub-selects
    return Package.objects.filter(pk__in=package_ids).update(
        latest_version_id=Subquery(latest_version_base.values("pk")[:1]),
        # Coalesce checks the subquery result; if None, it falls back to Value(True)
        supports_python3=Coalesce(
            Subquery(latest_version_base.values("supports_python3")[:1]),
            # Since python 2 support have been deprecated a long time ago, we default to True
            Value(True),
            output_field=BooleanField(),
        ),
    )


def _batch_update_commit_stats(package_ids: list[int], batch_size: int) -> int:
    """
    Update commit statistics for a batch of packages.

    Args:
        package_ids: Package IDs to update
        batch_size: Batch size for bulk_update

    Returns:
        Number of packages updated
    """
    if not package_ids:
        return 0

    stats = _aggregate_commit_stats(package_ids)

    # Load only required fields
    packages_to_update = []
    for package in Package.objects.filter(pk__in=package_ids).only(
        "pk", "last_commit_date", "commits_over_52w"
    ):
        package.last_commit_date = stats.last_commit_date.get(package.pk)
        package.commits_over_52w = stats.weekly_histogram.get(package.pk, [])
        packages_to_update.append(package)

    if packages_to_update:
        Package.objects.bulk_update(
            packages_to_update,
            fields=["last_commit_date", "commits_over_52w"],
            batch_size=batch_size,
        )

    return len(packages_to_update)


def update_package_latest_version(package: Package, save=True) -> bool:
    """
    Update the latest_version field for a single Package.

    Finds the most recent non-hidden Version and updates the foreign key.

    Args:
        package: Package instance to update

    Returns:
        True if updated, False if already current

    Example:
        >>> package = Package.objects.get(slug="requests")
        >>> if update_package_latest_version(package):
        ...     print(f"Updated to: {package.latest_version}")
    """
    latest_version = (
        Version.objects.filter(package=package, hidden=False)
        .order_by("-upload_time", "-created", "-pk")
        .first()
    )

    if not latest_version:
        return False

    package.latest_version = latest_version
    package.supports_python3 = latest_version.supports_python3

    if save:
        package.save(update_fields=["latest_version", "supports_python3"])

    return True


def update_package_commit_stats(package: Package, save=True) -> bool:
    """
    Update commit statistics for a single Package.

    Updates:
    - last_commit_date: Most recent commit date
    - commits_over_52w: 52-week histogram of commits

    Args:
        package: Package instance to update

    Returns:
        True if updated, False if already current

    Example:
        >>> package = Package.objects.get(slug="django")
        >>> if update_package_commit_stats(package):
        ...     print(f"Last commit: {package.last_commit_date}")
        ...     print(f"Commit histogram: {package.commits_over_52w}")
    """
    stats = _aggregate_commit_stats([package.pk])

    new_last_commit = stats.last_commit_date.get(package.pk)
    new_histogram = stats.weekly_histogram.get(package.pk, [])

    if (
        package.last_commit_date != new_last_commit
        or package.commits_over_52w != new_histogram
    ):
        package.last_commit_date = new_last_commit
        package.commits_over_52w = new_histogram

        if save:
            package.save(update_fields=["last_commit_date", "commits_over_52w"])

        return True

    return False


def update_package_stat_fields(
    package: Package,
    *,
    update_version: bool = True,
    update_commits: bool = True,
    save: bool = True,
) -> dict[str, bool]:
    """
    Update all stats fields for a single Package.

    Args:
        package: Package instance to update
        update_version: Whether to update latest_version
        update_commits: Whether to update commit statistics

    Returns:
        Dict with 'version_updated' and 'commits_updated' boolean values

    Example:
        >>> package = Package.objects.get(slug="numpy")
        >>> result = update_package_stat_fields(package)
        >>> print(f"Version: {result['version_updated']}, "
        ...       f"Commits: {result['commits_updated']}")
    """
    result = {"version_updated": False, "commits_updated": False}

    if update_version:
        result["version_updated"] = update_package_latest_version(package, save=False)

    if update_commits:
        result["commits_updated"] = update_package_commit_stats(package, save=False)

    if save and (result["version_updated"] or result["commits_updated"]):
        package.save()

    return result


def update_latest_version_bulk(
    packages_qs: QuerySet,
    *,
    batch_size: int = 1000,
    progress_callback: callable | None = None,
) -> UpdateResult:
    """
    Update latest_version for multiple packages efficiently.

    Processes in batches using single UPDATE query per batch.

    Args:
        packages_qs: QuerySet of Package objects
        batch_size: Packages per batch (default: 1000)
        progress_callback: Optional callback(processed: int, total: int)

    Returns:
        UpdateResult with operation statistics

    Example:
        >>> packages = Package.objects.filter(category="web")
        >>> result = update_latest_version_bulk(packages, batch_size=500)
        >>> print(f"Updated {result.updated_count}/{result.total_count}")

    Raises:
        ValueError: If batch_size < 1
    """
    if batch_size < 1:
        raise ValueError("batch_size must be at least 1")

    total_packages = packages_qs.count()
    total_updated = 0
    processed = 0

    for batch in iterate_in_batches(packages_qs, batch_size):
        total_updated += _batch_update_versions(batch)
        processed += len(batch)

        if progress_callback:
            progress_callback(processed, total_packages)

    return UpdateResult(
        updated_count=total_updated,
        total_count=total_packages,
        skipped_count=total_packages - total_updated,
    )


def update_commit_stats_bulk(
    packages_qs: QuerySet,
    *,
    batch_size: int = 1000,
    progress_callback: callable | None = None,
) -> UpdateResult:
    """
    Update commit statistics for multiple packages efficiently.

    Processes in batches, aggregating commit data and bulk updating.

    Args:
        packages_qs: QuerySet of Package objects
        batch_size: Packages per batch (default: 1000)
        progress_callback: Optional callback(processed: int, total: int)

    Returns:
        UpdateResult with operation statistics

    Example:
        >>> packages = Package.objects.all()
        >>> result = update_commit_stats_bulk(packages)
        >>> print(f"Success rate: {result.success_rate:.1f}%")

    Raises:
        ValueError: If batch_size < 1
    """
    if batch_size < 1:
        raise ValueError("batch_size must be at least 1")

    total_packages = packages_qs.count()
    total_updated = 0
    processed = 0

    for batch in iterate_in_batches(packages_qs, batch_size):
        total_updated += _batch_update_commit_stats(batch, batch_size)
        processed += len(batch)

        if progress_callback:
            progress_callback(processed, total_packages)

    return UpdateResult(
        updated_count=total_updated,
        total_count=total_packages,
        skipped_count=total_packages - total_updated,
    )


def update_package_stat_fields_bulk(
    packages_qs: QuerySet,
    *,
    batch_size: int = 1000,
    update_version: bool = True,
    update_commits: bool = True,
    progress_callback: callable | None = None,
) -> dict[Literal["version", "commits"], UpdateResult]:
    """
    Update all cached fields for multiple packages efficiently.

    Args:
        packages_qs: QuerySet of Package objects
        batch_size: Packages per batch (default: 1000)
        update_version: Whether to update latest_version
        update_commits: Whether to update commit statistics
        progress_callback: Optional callback for progress updates

    Returns:
        Dict with 'version' and/or 'commits' keys containing UpdateResults

    Example:
        >>> packages = Package.objects.filter(archived=False)
        >>> results = update_package_stat_fields_bulk(packages)
        >>> print(f"Versions: {results['version'].updated_count}")
        >>> print(f"Commits: {results['commits'].updated_count}")
    """
    results = {}

    if update_version:
        results["version"] = update_latest_version_bulk(
            packages_qs, batch_size=batch_size, progress_callback=progress_callback
        )

    if update_commits:
        results["commits"] = update_commit_stats_bulk(
            packages_qs, batch_size=batch_size, progress_callback=progress_callback
        )

    return results
