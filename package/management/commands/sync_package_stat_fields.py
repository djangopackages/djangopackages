from __future__ import annotations

import time
from collections import defaultdict
from datetime import timedelta
from typing import NamedTuple

import djclick as click
from django.db.models import Count, Max
from django.utils import timezone
from rich import print as rprint
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
)

from package.models import Commit, Package, Version


class UpdateResult(NamedTuple):
    updated_count: int
    total_count: int
    skipped_count: int

    @property
    def success_rate(self) -> float:
        if self.total_count == 0:
            return 0.0
        return (self.updated_count / self.total_count) * 100


def _display_result(result: UpdateResult, field_name: str, dry_run: bool) -> None:
    """
    Display formatted results of an update operation.
    """
    prefix = "Would update" if dry_run else "Updated"
    rprint(f"{prefix} {field_name} for {result.updated_count:,} package(s)")

    if result.skipped_count > 0:
        rprint(f"  [dim]Skipped {result.skipped_count:,} (no changes needed)[/dim]")

    if result.total_count > 0:
        rprint(f"  [dim]Success rate: {result.success_rate:.1f}%[/dim]")


def process_version_batch(packages: list[Package], dry_run: bool) -> tuple[int, int]:
    """
    Process a batch of packages to update version-related fields.
    Returns (updated_count, skipped_count).
    """
    latest_versions = (
        Version.objects.filter(package__in=packages, hidden=False)
        .exclude(upload_time=None)
        .order_by("package_id", "-upload_time")
        .distinct("package_id")
        .values("package_id", "pk", "supports_python3")
    )

    version_map = {v["package_id"]: v for v in latest_versions}
    to_update = []
    skipped = 0

    for package in packages:
        v_data = version_map.get(package.pk)
        changed = False

        if v_data:
            new_version_id = v_data["pk"]
            new_supports_py3 = v_data["supports_python3"]

            if package.latest_version_id != new_version_id:
                package.latest_version_id = new_version_id
                changed = True

            # Sync supports_python3 from latest version
            if package.supports_python3 != new_supports_py3:
                package.supports_python3 = new_supports_py3
                changed = True

        if changed:
            to_update.append(package)
        else:
            skipped += 1

    if to_update and not dry_run:
        Package.objects.bulk_update(to_update, ["latest_version", "supports_python3"])

    return len(to_update), skipped


def process_commit_batch(packages: list[Package], dry_run: bool) -> tuple[int, int]:
    """
    Process a batch of packages to update commit-related fields.
    Returns (updated_count, skipped_count).
    """
    reference_now = timezone.now()
    cutoff = reference_now - timedelta(weeks=52)

    # 1. Fetch Aggregates: commit_count, last_commit_date
    stats = (
        Commit.objects.filter(package__in=packages)
        .values("package_id")
        .annotate(count=Count("id"), last_date=Max("commit_date"))
    )
    stats_map = {s["package_id"]: s for s in stats}

    # 2. Fetch Recent Commits for Histogram: commits_over_52w
    # Fetch only needed fields for packages that have commits in last 52 weeks
    recent_commits = Commit.objects.filter(
        package__in=packages, commit_date__gt=cutoff
    ).values("package_id", "commit_date")

    # Calculate histograms in memory
    histograms = defaultdict(lambda: [0] * 52)
    for c in recent_commits:
        pid = c["package_id"]
        cdate = c["commit_date"]
        # Calculate weeks ago (0 = this week, 51 = 52 weeks ago)
        age_weeks = (reference_now - cdate).days // 7
        if 0 <= age_weeks < 52:
            histograms[pid][age_weeks] += 1

    to_update = []
    skipped = 0

    for package in packages:
        s = stats_map.get(package.pk)
        changed = False

        # Update commit_count
        new_count = s["count"] if s else 0
        if package.commit_count != new_count:
            package.commit_count = new_count
            changed = True

        # Update last_commit_date
        new_last_date = s["last_date"] if s else None
        if package.last_commit_date != new_last_date:
            package.last_commit_date = new_last_date
            changed = True

        # Update commits_over_52w
        # weeks array is [week0_count, ..., week51_count]
        # We reverse it to store as [oldest_week, ..., newest_week]
        raw_weeks = histograms[package.pk]  # defaults to [0]*52 if no recent commits
        new_histogram = list(reversed(raw_weeks))

        if package.commits_over_52w != new_histogram:
            package.commits_over_52w = new_histogram
            changed = True

        if changed:
            to_update.append(package)
        else:
            skipped += 1

    if to_update and not dry_run:
        Package.objects.bulk_update(
            to_update, ["commit_count", "last_commit_date", "commits_over_52w"]
        )

    return len(to_update), skipped


def update_latest_version_bulk(
    packages_qs,
    batch_size,
    progress_callback,
    dry_run=False,
) -> UpdateResult:
    total_updated = 0
    total_processed = 0
    total_skipped = 0

    # Create iterator
    iterator = packages_qs.iterator(chunk_size=batch_size)
    batch = []

    for package in iterator:
        batch.append(package)
        if len(batch) >= batch_size:
            updated, skipped = process_version_batch(batch, dry_run)
            total_updated += updated
            total_skipped += skipped
            total_processed += len(batch)
            if progress_callback:
                progress_callback(total_processed, None)
            batch = []

    if batch:
        updated, skipped = process_version_batch(batch, dry_run)
        total_updated += updated
        total_skipped += skipped
        total_processed += len(batch)
        if progress_callback:
            progress_callback(total_processed, None)

    return UpdateResult(total_updated, total_processed, total_skipped)


def update_commit_stats_bulk(
    packages_qs,
    batch_size,
    progress_callback,
    dry_run=False,
) -> UpdateResult:
    total_updated = 0
    total_processed = 0
    total_skipped = 0

    iterator = packages_qs.iterator(chunk_size=batch_size)
    batch = []

    for package in iterator:
        batch.append(package)
        if len(batch) >= batch_size:
            updated, skipped = process_commit_batch(batch, dry_run)
            total_updated += updated
            total_skipped += skipped
            total_processed += len(batch)
            if progress_callback:
                progress_callback(total_processed, None)
            batch = []

    if batch:
        updated, skipped = process_commit_batch(batch, dry_run)
        total_updated += updated
        total_skipped += skipped
        total_processed += len(batch)
        if progress_callback:
            progress_callback(total_processed, None)

    return UpdateResult(total_updated, total_processed, total_skipped)


@click.command()
@click.option(
    "--package-id",
    "package_ids",
    multiple=True,
    type=int,
    help="Specific package ID(s) to process",
)
@click.option(
    "--slug",
    "slugs",
    multiple=True,
    type=str,
    help="Specific package slug(s) to process",
)
@click.option(
    "--limit",
    default=None,
    type=int,
    help="Maximum number of packages to process",
)
@click.option(
    "--batch-size",
    default=1000,
    type=int,
    help="Number of packages per batch (default: 1000)",
)
@click.option(
    "--commits/--no-commits",
    default=True,
    help="Update commit statistics (default: enabled)",
)
@click.option(
    "--versions/--no-versions",
    default=True,
    help="Update latest_version (default: enabled)",
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Preview changes without applying them",
)
def command(
    package_ids: tuple[int, ...],
    slugs: tuple[str, ...],
    limit: int | None,
    batch_size: int,
    commits: bool,
    versions: bool,
    dry_run: bool,
):
    """
    Efficiently backfill cached Package fields.

    Updates:
    - Package.commits_over_52w: 52-week commit histogram
    - Package.last_commit_date: Most recent commit date
    - Package.commit_count: Total number of commits
    - Package.latest_version: Latest non-hidden Version
    - Package.supports_python3: Python 3 support flag

    This command aggregates data from existing Commit and Version records.
    All operations are batched for efficiency.
    """
    # Validate inputs
    if batch_size <= 0:
        raise click.ClickException("--batch-size must be greater than 0")

    if not commits and not versions:
        raise click.ClickException(
            "At least one update type must be enabled. "
            "Remove --no-commits and/or --no-versions."
        )

    # Build queryset
    packages_qs = Package.objects.all()

    if package_ids:
        packages_qs = packages_qs.filter(pk__in=package_ids)
    if slugs:
        packages_qs = packages_qs.filter(slug__in=slugs)
    if limit is not None:
        packages_qs = packages_qs[:limit]

    packages_qs = packages_qs.order_by("pk")

    # Get total count
    total = packages_qs.count()
    rprint(f"\n[bold]Found {total:,} package(s) to process[/bold]")

    if total == 0:
        rprint("[yellow]No packages to process[/yellow]")
        return

    # Display applied filters
    filters = []
    if package_ids:
        filters.append(f"{len(package_ids)} package ID(s)")
    if slugs:
        filters.append(f"{len(slugs)} slug(s)")
    if limit:
        filters.append(f"limit of {limit:,}")

    if filters:
        rprint(f"[dim]Filters: {', '.join(filters)}[/dim]")

    if dry_run:
        rprint("\n[yellow bold]DRY RUN MODE - No changes will be made[/yellow bold]")

    rprint(f"[dim]Batch size: {batch_size:,}[/dim]\n")

    # Start timing
    start_time = time.perf_counter()

    # Update latest_version
    if versions:
        rprint("[bold]Updating latest_version and supports_python3…[/bold]")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
        ) as progress:
            task = progress.add_task("Processing packages", total=total)

            def update_progress(processed: int, _total: int | None):
                progress.update(task, completed=processed)

            result = update_latest_version_bulk(
                packages_qs,
                batch_size=batch_size,
                progress_callback=update_progress,
                dry_run=dry_run,
            )

        _display_result(result, "latest_version/supports_python3", dry_run)
        rprint()

    # Update commit statistics
    if commits:
        rprint("[bold]Updating commit statistics…[/bold]")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
        ) as progress:
            task = progress.add_task("Processing packages", total=total)

            def update_progress(processed: int, _total: int | None):
                progress.update(task, completed=processed)

            result = update_commit_stats_bulk(
                packages_qs,
                batch_size=batch_size,
                progress_callback=update_progress,
                dry_run=dry_run,
            )

        _display_result(result, "commit statistics", dry_run)
        rprint()

    # Display summary
    elapsed = time.perf_counter() - start_time
    rprint(f"[bold green]✓ Completed in {elapsed:.2f}s[/bold green]")

    if dry_run:
        rprint("\n[dim]Run without --dry-run to apply changes[/dim]")
