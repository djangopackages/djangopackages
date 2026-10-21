from __future__ import annotations

import djclick as click
from django.conf import settings
from rich import print as rprint

from package.models import Package
from probes.checkouts import (
    CheckoutError,
    checkout_path,
    checkout_size,
    discard_checkout,
    is_cloneable,
    scannable_packages,
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
@click.option(
    "--min-score",
    default=0,
    type=int,
    help=(
        "Lowest package score to include. Below zero means roughly thirty "
        "months without a commit; pass -500 to reach those too (default: 0)"
    ),
)
@click.option(
    "--max-mb",
    default=None,
    type=int,
    help=(
        "Discard a checkout bigger than this and mark the package as one "
        "we do not want, so later runs skip it. Sizes are long tailed: "
        "the median checkout is around 11MB and the largest is over a "
        "gigabyte, so a cap costs few packages and most of the disk"
    ),
)
@click.option("--dry-run", is_flag=True, help="List what would be fetched")
def command(
    slugs: tuple[str, ...],
    limit: int | None,
    depth: int,
    timeout: int,
    missing_only: bool,
    min_score: int,
    max_mb: int | None,
    dry_run: bool,
):
    """Clone or update local git checkouts of the packages we index.

    Checkouts live under PACKAGE_REPO_ROOT, one directory per slug, and
    are refreshed in place. Packages whose repo_url points somewhere we
    cannot clone from are skipped and counted, so a zero result reads as
    "nothing to clone" rather than "nothing found".
    """
    # An explicit --slug is an explicit request, so it reaches packages
    # the default set leaves out.
    queryset = (
        Package.objects.order_by("-score", "title")
        if slugs
        else scannable_packages(min_score=min_score)
    )
    if slugs:
        queryset = queryset.filter(slug__in=slugs)

    root = settings.PACKAGE_REPO_ROOT
    if not dry_run:
        root.mkdir(parents=True, exist_ok=True)

    cloned = updated = skipped = failed = too_big = 0
    reclaimed = 0

    # The limit counts packages we actually fetched, not rows we looked
    # at. Slicing the queryset instead would take the same highest
    # scoring rows every run, so --missing-only would skip all of them
    # and never reach anything new.
    for package in queryset.iterator():
        if limit and cloned + updated + failed >= limit:
            break

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

        # Measured every time, not just against a cap: the size is worth
        # knowing on its own, and it is what any later cap reads.
        size = checkout_size(path)
        package.probe_bytes = size

        if max_mb is not None and size > max_mb * 1024 * 1024:
            # Cloning it was the only way to find out how big it is, so
            # the cost is already paid; what the cap saves is keeping it
            # and fetching it again on every run after this.
            discard_checkout(path)
            package.probe_wanted = False
            package.probe_wanted_note = f"checkout is {size // (1024 * 1024):,}MB"
            package.probe_bytes = size
            package.save(
                update_fields=["probe_wanted", "probe_wanted_note", "probe_bytes"]
            )
            too_big += 1
            reclaimed += size
            rprint(
                f"[yellow]{package.slug}[/yellow] "
                f"{size // (1024 * 1024):,}MB over the {max_mb:,}MB cap, discarded"
            )
            continue

        package.save(update_fields=["probe_bytes"])

        if action == "cloned":
            cloned += 1
        else:
            updated += 1

    if dry_run:
        return

    rprint(
        f"cloned {cloned:,}  updated {updated:,}  "
        f"skipped {skipped:,}  failed {failed:,}  too big {too_big:,}"
    )
    if too_big:
        rprint(f"[dim]{reclaimed // (1024 * 1024):,}MB discarded by the cap[/dim]")
    rprint(f"[dim]checkouts in {root}[/dim]")
