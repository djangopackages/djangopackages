"""Keep `Package.score` current.

The number itself comes from `package.scoring`; this module is the glue
that reads a package, computes it, and writes it back only when it
changed. See #1563 for the switch from the old stars-minus-penalties
formula.
"""

from __future__ import annotations

from dataclasses import dataclass

from django.db.models import QuerySet

from package.models import Package
from package.scoring import ScoreInputs, calculate_score
from package.utils import iterate_in_batches

# The columns `ScoreInputs.from_package` reads, for `.only()`.
SCORE_FIELDS = (
    "pk",
    "score",
    "repo_watchers",
    "pypi_downloads",
    "last_commit_date",
    "date_deprecated",
    "date_repo_archived",
    "latest_version__upload_time",
)


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


def _batch_update_scores(package_ids: list[int]) -> int:
    """Recompute and bulk-save the scores of one batch. Returns how many changed."""
    if not package_ids:
        return 0

    packages_to_update = []
    packages = (
        Package.objects.filter(pk__in=package_ids)
        .select_related("latest_version")
        .only(*SCORE_FIELDS)
    )
    for package in packages:
        new_score = calculate_score(ScoreInputs.from_package(package))
        if package.score != new_score:
            package.score = new_score
            packages_to_update.append(package)

    if packages_to_update:
        Package.objects.bulk_update(
            packages_to_update, fields=["score"], batch_size=500
        )

    return len(packages_to_update)


def update_package_score(package: Package, save: bool = True) -> bool:
    """
    Update the score field for a single Package.

    Only updates if the calculated score differs from the current score.
    Reads `package.latest_version`, so load it with `select_related` when
    calling this in a loop.

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
    new_score = calculate_score(ScoreInputs.from_package(package))

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

    Processes packages in batches, loading only the columns the score
    reads. Only updates packages whose scores have changed.

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
