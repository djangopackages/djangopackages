from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import timedelta
from collections.abc import Iterator

import djclick as click
from django.db import transaction
from django.db.models import Max, OuterRef, Subquery, QuerySet
from django.utils import timezone
from rich import print
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
)

from package.models import Commit, Package, Version


@dataclass(frozen=True)
class CommitRollups:
    last_commit_date: dict[int, timezone.datetime | None]
    commits_over_52w: dict[int, list[int]]


def _chunked_iterator(queryset: QuerySet, chunk_size: int) -> Iterator[list]:
    """Yield chunks of objects from a queryset to manage memory efficiently."""
    queryset = queryset.order_by("pk")
    batch = []

    for obj in queryset.iterator(chunk_size=chunk_size):
        batch.append(obj)
        if len(batch) >= chunk_size:
            yield batch
            batch = []

    if batch:
        yield batch


def _build_commit_rollups_batch(package_ids: list[int]) -> CommitRollups:
    """Build commit rollups for a batch of packages to reduce memory usage."""
    now_dt = timezone.now()
    cutoff = now_dt - timedelta(weeks=52)

    # Last commit date - single query with indexed filter
    last_commit_dt = (
        Commit.objects.filter(package_id__in=package_ids)
        .values("package_id")
        .annotate(max_dt=Max("commit_date"))
        .values_list("package_id", "max_dt")
    )
    last_commit_date: dict[int, timezone.datetime | None] = dict(last_commit_dt)

    # Initialize buckets only for packages with commits
    buckets_by_package: dict[int, list[int]] = {}

    # Stream recent commits with date range filter
    recent_commits = (
        Commit.objects.filter(
            package_id__in=package_ids, commit_date__gte=cutoff, commit_date__lte=now_dt
        )
        .values_list("package_id", "commit_date")
        .iterator(chunk_size=5_000)
    )

    for package_id, commit_dt in recent_commits:
        if commit_dt is None:
            continue

        age_days = (now_dt - commit_dt).days
        if age_days < 0:
            continue

        age_weeks = age_days // 7
        if age_weeks < 52:
            if package_id not in buckets_by_package:
                buckets_by_package[package_id] = [0] * 52
            buckets_by_package[package_id][age_weeks] += 1

    # Convert to comma-separated strings (reversed for storage)
    commits_over_52w: dict[int, list[int]] = {
        package_id: list(reversed(weeks))
        for package_id, weeks in buckets_by_package.items()
    }

    return CommitRollups(
        last_commit_date=last_commit_date, commits_over_52w=commits_over_52w
    )


def _update_latest_versions_batched(
    packages_qs: QuerySet, batch_size: int, dry_run: bool
) -> int:
    """Update latest_version in batches to avoid overwhelming the database."""
    total_updated = 0

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
    ) as progress:
        total_packages = packages_qs.count()
        task = progress.add_task("Updating latest_version", total=total_packages)

        # Process in batches using primary keys
        for package_ids_batch in _chunked_iterator(
            packages_qs.values_list("pk", flat=True), batch_size
        ):
            if dry_run:
                total_updated += len(package_ids_batch)
            else:
                # Build subquery for this batch only
                batch_packages = Package.objects.filter(pk__in=package_ids_batch)
                latest_version_sq = (
                    Version.objects.filter(package_id=OuterRef("pk"), hidden=False)
                    .order_by("-upload_time", "-created", "-pk")
                    .values("pk")[:1]
                )

                # Update only this batch
                with transaction.atomic():
                    updated = batch_packages.update(
                        latest_version_id=Subquery(latest_version_sq)
                    )
                    total_updated += updated

            progress.update(task, advance=len(package_ids_batch))

    return total_updated


def _update_commit_rollups_batched(
    packages_qs: QuerySet, batch_size: int, dry_run: bool
) -> int:
    """Update commit rollups in batches to minimize memory usage."""
    total_updated = 0
    fields = ["commits_over_52w", "last_commit_date"]

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
    ) as progress:
        total_packages = packages_qs.count()
        task = progress.add_task("Updating commit rollups", total=total_packages)

        # Process packages in batches
        for package_ids_batch in _chunked_iterator(
            packages_qs.values_list("pk", flat=True), batch_size
        ):
            # Build rollups for this batch only
            rollups = _build_commit_rollups_batch(package_ids_batch)

            # Load only the packages in this batch with minimal fields
            packages_to_update = []
            for package in Package.objects.filter(pk__in=package_ids_batch).only(
                "pk", *fields
            ):
                package.last_commit_date = rollups.last_commit_date.get(package.pk)
                package.commits_over_52w = rollups.commits_over_52w.get(package.pk, [])
                packages_to_update.append(package)

            # Bulk update this batch
            if not dry_run and packages_to_update:
                with transaction.atomic():
                    Package.objects.bulk_update(
                        packages_to_update, fields=fields, batch_size=batch_size
                    )

            total_updated += len(packages_to_update)
            progress.update(task, advance=len(package_ids_batch))

    return total_updated


@click.command()
@click.option("--package-id", "package_ids", multiple=True, type=int)
@click.option("--slug", "slugs", multiple=True, type=str)
@click.option("--limit", default=None, type=int)
@click.option(
    "--batch-size",
    default=1000,
    type=int,
    help="Number of packages to process per batch",
)
@click.option(
    "--commits/--no-commits",
    default=True,
    help="Update commits_over_52w and last_commit_date",
)
@click.option("--versions/--no-versions", default=True, help="Update latest_version")
@click.option("--dry-run", is_flag=True, default=False)
def command(
    package_ids: tuple[int, ...],
    slugs: tuple[str, ...],
    limit: int | None,
    batch_size: int,
    commits: bool,
    versions: bool,
    dry_run: bool,
):
    """Efficiently backfill cached Package fields.

    Updates:
    - Package.commits_over_52 (52-week commit histogram)
    - Package.last_commit_date (max Commit.commit_date)
    - Package.latest_version (latest Version by upload_time)

    This command does NOT fetch data from external services; it only aggregates
    from existing database rows. All operations are batched to handle large
    datasets efficiently with minimal memory and database load.
    """

    if batch_size <= 0:
        raise click.ClickException("--batch-size must be > 0")

    if batch_size > 10_000:
        print(
            f"[yellow]Warning: batch-size of {batch_size} is very large. Consider using 1000-5000 for better performance.[/yellow]"
        )

    # Build base queryset
    packages_qs = Package.objects.all()

    if package_ids:
        packages_qs = packages_qs.filter(pk__in=package_ids)
    if slugs:
        packages_qs = packages_qs.filter(slug__in=slugs)
    if limit is not None:
        packages_qs = packages_qs[:limit]

    packages_qs = packages_qs.order_by("pk")

    total = packages_qs.count()
    print(f"Found {total:,} package(s) to process")

    if total == 0:
        print("No packages to process")
        return

    if dry_run:
        print("[yellow]DRY RUN MODE - No changes will be made[/yellow]")

    started = time.perf_counter()

    # Update latest_version in batches
    if versions:
        print("\n[bold]Updating latest_version…[/bold]")
        updated = _update_latest_versions_batched(packages_qs, batch_size, dry_run)
        status = "Would update" if dry_run else "Updated"
        print(f"{status} latest_version for {updated:,} package(s)")

    # Update commit rollups in batches
    if commits:
        print("\n[bold]Aggregating commit rollups…[/bold]")
        updated = _update_commit_rollups_batched(packages_qs, batch_size, dry_run)
        status = "Would update" if dry_run else "Updated"
        print(f"{status} commit rollups for {updated:,} package(s)")

    elapsed = time.perf_counter() - started
    print(f"\n[bold green]Done in {elapsed:0.2f}s[/bold green]")
