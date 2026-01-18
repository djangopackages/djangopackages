from __future__ import annotations

import time

import djclick as click
from rich import print as rprint
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
)

from package.models import Package
from package.stats_updater import (
    update_latest_version_bulk,
    update_commit_stats_bulk,
    UpdateResult,
)


def _display_result(result: UpdateResult, field_name: str, dry_run: bool) -> None:
    """
    Display formatted results of an update operation.

    Args:
        result: UpdateResult from the operation
        field_name: Name of the field being updated
        dry_run: Whether this was a dry run
    """
    prefix = "Would update" if dry_run else "Updated"
    rprint(f"{prefix} {field_name} for {result.updated_count:,} package(s)")

    if result.skipped_count > 0:
        rprint(f"  [dim]Skipped {result.skipped_count:,} (no changes needed)[/dim]")

    if result.total_count > 0:
        rprint(f"  [dim]Success rate: {result.success_rate:.1f}%[/dim]")


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
    - Package.latest_version: Latest non-hidden Version

    This command aggregates data from existing Commit and Version records.
    All operations are batched for efficiency.

    Examples:

        # Update all packages
        python manage.py backfill_package_fields

        # Update specific packages
        python manage.py backfill_package_fields --package-id 1 --package-id 2

        # Update by slug with custom batch size
        python manage.py backfill_package_fields --slug django --batch-size 500

        # Preview changes
        python manage.py backfill_package_fields --dry-run

        # Only update commit data
        python manage.py backfill_package_fields --no-versions
    """
    # Validate inputs
    if batch_size <= 0:
        raise click.ClickException("--batch-size must be greater than 0")

    if batch_size > 10_000:
        rprint(
            f"[yellow]Warning: batch-size of {batch_size:,} is very large. "
            f"Consider 1,000-5,000 for optimal performance.[/yellow]"
        )

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
        rprint("[bold]Updating latest_version…[/bold]")

        if dry_run:
            result = UpdateResult(
                updated_count=total, total_count=total, skipped_count=0
            )
        else:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
            ) as progress:
                task = progress.add_task("Processing packages", total=total)

                def update_progress(processed: int, _total: int):
                    progress.update(task, completed=processed)

                result = update_latest_version_bulk(
                    packages_qs,
                    batch_size=batch_size,
                    progress_callback=update_progress,
                )

        _display_result(result, "latest_version", dry_run)
        rprint()

    # Update commit statistics
    if commits:
        rprint("[bold]Updating commit statistics…[/bold]")

        if dry_run:
            result = UpdateResult(
                updated_count=total, total_count=total, skipped_count=0
            )
        else:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
            ) as progress:
                task = progress.add_task("Processing packages", total=total)

                def update_progress(processed: int, _total: int):
                    progress.update(task, completed=processed)

                result = update_commit_stats_bulk(
                    packages_qs,
                    batch_size=batch_size,
                    progress_callback=update_progress,
                )

        _display_result(result, "commit statistics", dry_run)
        rprint()

    # Display summary
    elapsed = time.perf_counter() - start_time
    rprint(f"[bold green]✓ Completed in {elapsed:.2f}s[/bold green]")

    if dry_run:
        rprint("\n[dim]Run without --dry-run to apply changes[/dim]")
