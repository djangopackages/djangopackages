from __future__ import annotations

import djclick as click
from django.conf import settings
from rich import print as rprint

from package.models import Package
from package.repo_checkouts import (
    CheckoutError,
    checkout_path,
    is_cloneable,
    sync_checkout,
)


@click.command()
@click.option("--slug", "slugs", multiple=True, help="Specific package slug(s)")
@click.option("--limit", default=None, type=int, help="Maximum packages to process")
@click.option(
    "--depth",
    default=1,
    type=int,
    help="Clone depth; 0 for full history (default: 1)",
)
@click.option(
    "--timeout", default=300, type=int, help="Seconds per git command (default: 300)"
)
@click.option(
    "--missing-only",
    is_flag=True,
    help="Only clone packages with no checkout yet, skipping updates",
)
@click.option("--dry-run", is_flag=True, help="List what would be fetched")
def command(
    slugs: tuple[str, ...],
    limit: int | None,
    depth: int,
    timeout: int,
    missing_only: bool,
    dry_run: bool,
):
    """Clone or update local git checkouts of the packages we index.

    Checkouts live under PACKAGE_REPO_ROOT, one directory per slug, and
    are refreshed in place. Packages whose repo_url points somewhere we
    cannot clone from are skipped and counted, so a zero result reads as
    "nothing to clone" rather than "nothing found".
    """
    queryset = Package.objects.order_by("-score", "title")
    if slugs:
        queryset = queryset.filter(slug__in=slugs)
    if limit:
        queryset = queryset[:limit]

    root = settings.PACKAGE_REPO_ROOT
    if not dry_run:
        root.mkdir(parents=True, exist_ok=True)

    cloned = updated = skipped = failed = 0

    for package in queryset:
        if not is_cloneable(package.repo_url):
            skipped += 1
            continue

        path = checkout_path(package)
        exists = (path / ".git").is_dir()

        if missing_only and exists:
            skipped += 1
            continue

        if dry_run:
            rprint(f"[dim]would {'update' if exists else 'clone'}[/dim] {package.slug}")
            continue

        try:
            _, action = sync_checkout(package, depth=depth, timeout=timeout)
        except CheckoutError as exc:
            failed += 1
            rprint(f"[red]{package.slug}[/red] {exc}")
            continue

        if action == "cloned":
            cloned += 1
        else:
            updated += 1

    if dry_run:
        return

    rprint(
        f"cloned {cloned:,}  updated {updated:,}  "
        f"skipped {skipped:,}  failed {failed:,}"
    )
    rprint(f"[dim]checkouts in {root}[/dim]")
