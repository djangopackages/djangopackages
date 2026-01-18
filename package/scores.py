from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime

from dateutil import relativedelta
from django.db.models import QuerySet
from django.utils.timezone import now

from package.models import Package
from package.utils import iterate_in_batches


@dataclass(frozen=True)
class UpdateResult:
    """Result of a score update operation."""

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


@dataclass(frozen=True)
class PackageScoreData:
    """Data needed to calculate a package score."""

    pk: int
    repo_watchers: int
    last_commit_date: datetime | None
    supports_python3: bool


def _calculate_score(
    repo_watchers: int, last_commit_date: datetime | None, supports_python3: bool
) -> int:
    """
    Calculate package score based on watchers, update recency, and Python 3 support.

    Scoring rules:
    - Base score: repo_watchers (GitHub stars)
    - Penalty: 10% of stars for each 3 months since last update
    - Penalty: 30% of stars (max 1000) if no Python 3 support
    - Minimum score: -500

    Args:
        repo_watchers: Number of GitHub watchers/stars
        last_commit_date: DateTime of last commit
        supports_python3: Whether package supports Python 3

    Returns:
        Calculated score (minimum -500)
    """
    # Calculate months since last update
    if last_commit_date:
        delta = relativedelta.relativedelta(now(), last_commit_date)
        delta_months = (delta.years * 12) + delta.months
        last_commit_date_penalty = math.modf(delta_months / 3)[1] * repo_watchers / 10
    else:
        # No update date means very old package - maximum penalty
        last_commit_date_penalty = repo_watchers / 10

    # Python 3 support penalty
    python_3_penalty = 0 if supports_python3 else min(repo_watchers * 30 / 100, 1000)

    # Calculate final score with floor at -500
    return max(-500, int(repo_watchers - last_commit_date_penalty - python_3_penalty))


def _fetch_bulk_score_data(package_ids: list[int]) -> dict[int, PackageScoreData]:
    """
    Efficiently fetch score calculation data for multiple packages.

    Uses prefetch_related to minimize queries and only loads necessary fields.

    Args:
        package_ids: List of package IDs to fetch data for

    Returns:
        Dictionary mapping package_id to PackageScoreData
    """
    if not package_ids:
        return {}

    # Load packages with minimal fields + prefetched versions
    packages = Package.objects.filter(pk__in=package_ids).only(
        "pk", "repo_watchers", "last_commit_date", "supports_python3"
    )

    score_data = {}
    for package in packages:
        score_data[package.pk] = PackageScoreData(
            pk=package.pk,
            repo_watchers=package.repo_watchers,
            last_commit_date=package.last_commit_date,
            supports_python3=package.supports_python3,
        )

    return score_data


def _batch_update_scores(package_ids: list[int]) -> int:
    """
    Update scores for a batch of packages using bulk_update.

    Args:
        package_ids: Package IDs to update

    Returns:
        Number of packages updated
    """
    if not package_ids:
        return 0

    # Fetch all needed data efficiently
    score_data = _fetch_bulk_score_data(package_ids)

    # Load packages and calculate new scores
    packages_to_update = []
    for package in Package.objects.filter(pk__in=package_ids).only("pk", "score"):
        data = score_data.get(package.pk)

        if not data:
            continue

        new_score = _calculate_score(
            repo_watchers=data.repo_watchers,
            last_commit_date=data.last_commit_date,
            supports_python3=data.supports_python3,
        )

        # Only update if score changed
        if package.score != new_score:
            package.score = new_score
            packages_to_update.append(package)

    # Bulk update if there are changes
    if packages_to_update:
        Package.objects.bulk_update(
            packages_to_update, fields=["score"], batch_size=500
        )

    return len(packages_to_update)


def update_package_score(package: Package, save: bool = True) -> bool:
    """
    Update the score field for a single Package.

    Calculates score based on repo watchers, last update time, and Python 3 support.
    Only updates if the calculated score differs from the current score.

    Args:
        package: Package instance to update
        save: Whether to save the package after updating the score (default: True)
    Returns:
        True if updated, False if already current

    Example:
        >>> package = Package.objects.get(slug="django")
        >>> if update_package_score(package):
        ...     print(f"New score: {package.score}")
    """
    data = PackageScoreData(
        pk=package.pk,
        repo_watchers=package.repo_watchers,
        last_commit_date=package.last_commit_date,
        supports_python3=package.supports_python3,
    )

    new_score = _calculate_score(
        repo_watchers=data.repo_watchers,
        last_commit_date=data.last_commit_date,
        supports_python3=data.supports_python3,
    )

    if package.score != new_score:
        package.score = new_score

        if save:
            package.save(update_fields=["score"])

        return True

    return False


def update_package_scores_bulk(
    packages_qs: QuerySet,
    *,
    batch_size: int = 500,
    progress_callback: callable | None = None,
) -> UpdateResult:
    """
    Update scores for multiple packages efficiently.

    Processes packages in batches, prefetching all required data to minimize
    database queries. Only updates packages whose scores have changed.

    Args:
        packages_qs: QuerySet of Package objects
        batch_size: Packages per batch (default: 500)
        progress_callback: Optional callback(processed: int, total: int)

    Returns:
        UpdateResult with operation statistics

    Example:
        >>> packages = Package.objects.filter(repo_watchers__gt=100)
        >>> result = update_package_scores_bulk(packages)
        >>> print(f"Updated {result.updated_count}/{result.total_count}")
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
        total_updated += _batch_update_scores(batch)
        processed += len(batch)

        if progress_callback:
            progress_callback(processed, total_packages)

    return UpdateResult(
        updated_count=total_updated,
        total_count=total_packages,
        skipped_count=total_packages - total_updated,
    )
