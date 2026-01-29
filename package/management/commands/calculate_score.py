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
from package.scores import update_package_scores_bulk, UpdateResult


def _display_result(result: UpdateResult, dry_run: bool) -> None:
    """
    Display formatted results of the score update operation.

    Args:
        result: UpdateResult from the operation
        dry_run: Whether this was a dry run
    """
    prefix = "Would update" if dry_run else "Updated"
    rprint(f"{prefix} scores for {result.updated_count:,} package(s)")

    if result.skipped_count > 0:
        rprint(f"  [dim]Skipped {result.skipped_count:,} (scores unchanged)[/dim]")

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
    default=500,
    type=int,
    help="Number of packages per batch (default: 500)",
)
@click.option(
    "--min-watchers",
    default=None,
    type=int,
    help="Only process packages with at least this many watchers",
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
    min_watchers: int | None,
    dry_run: bool,
):
    """
    Calculate and update package scores efficiently.

    Score calculation rules:
    - Base score: repo_watchers (GitHub stars)
    - Penalty: 10% of stars for each 3 months since last update
    - Penalty: 30% of stars (max 1000) if no Python 3 support
    - Minimum score: -500

    Examples:

        # Update all packages
        python manage.py calculate_score

        # Update specific packages
        python manage.py calculate_score --package-id 1 --package-id 2

        # Update packages by slug
        python manage.py calculate_score --slug django --slug requests

        # Only update popular packages (100+ stars)
        python manage.py calculate_score --min-watchers 100

        # Preview changes without saving
        python manage.py calculate_score --dry-run

        # Custom batch size for large datasets
        python manage.py calculate_score --batch-size 1000
    """
    # Validate inputs
    if batch_size <= 0:
        raise click.ClickException("--batch-size must be greater than 0")

    if batch_size > 5000:
        rprint(
            f"[yellow]Warning: batch-size of {batch_size:,} is very large. "
            f"Consider 500-1000 for optimal performance.[/yellow]"
        )

    # Build queryset
    packages_qs = Package.objects.all()

    if package_ids:
        packages_qs = packages_qs.filter(pk__in=package_ids)
    if slugs:
        packages_qs = packages_qs.filter(slug__in=slugs)
    if min_watchers is not None:
        packages_qs = packages_qs.filter(repo_watchers__gte=min_watchers)
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
    if min_watchers is not None:
        filters.append(f"min {min_watchers:,} watchers")
    if limit:
        filters.append(f"limit of {limit:,}")

    if filters:
        rprint(f"[dim]Filters: {', '.join(filters)}[/dim]")

    if dry_run:
        rprint("\n[yellow bold]DRY RUN MODE - No changes will be made[/yellow bold]")

    rprint(f"[dim]Batch size: {batch_size:,}[/dim]\n")

    # Start timing
    start_time = time.perf_counter()

    # Update scores
    rprint("[bold]Calculating and updating package scores…[/bold]")

    if dry_run:
        # For dry run, just count without updating
        result = UpdateResult(updated_count=total, total_count=total, skipped_count=0)
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

            result = update_package_scores_bulk(
                packages_qs, batch_size=batch_size, progress_callback=update_progress
            )

    _display_result(result, dry_run)
    rprint()

    # Display summary
    elapsed = time.perf_counter() - start_time
    rprint(f"[bold green]✓ Completed in {elapsed:.2f}s[/bold green]")

    if dry_run:
        rprint("\n[dim]Run without --dry-run to apply changes[/dim]")
    else:
        avg_time = (elapsed / total * 1000) if total > 0 else 0
        rprint(f"[dim]Average: {avg_time:.2f}ms per package[/dim]")
