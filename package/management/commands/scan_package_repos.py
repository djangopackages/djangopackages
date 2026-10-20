from __future__ import annotations

from collections import Counter

import djclick as click
from django.conf import settings
from rich import print as rprint

from package.models import Package
from package.repo_checkouts import checkout_path, scan_checkout


@click.command()
@click.option("--slug", "slugs", multiple=True, help="Specific package slug(s)")
@click.option("--limit", default=None, type=int, help="Maximum packages to scan")
@click.option(
    "--package",
    "scan_packages",
    multiple=True,
    default=("django",),
    help="Top-level import name(s) to count (default: django)",
)
@click.option(
    "--top", default=20, type=int, help="Symbols to show per package (default: 20)"
)
@click.option(
    "--totals-only", is_flag=True, help="Only print the roll-up across all packages"
)
def command(
    slugs: tuple[str, ...],
    limit: int | None,
    scan_packages: tuple[str, ...],
    top: int,
    totals_only: bool,
):
    """Count which Django APIs the checked out packages actually use.

    Reads the checkouts that sync_package_repos produced; it never
    touches the network. Packages with no checkout are counted as
    missing rather than treated as using nothing.
    """
    queryset = Package.objects.order_by("-score", "title")
    if slugs:
        queryset = queryset.filter(slug__in=slugs)
    if limit:
        queryset = queryset[:limit]

    overall: Counter[str] = Counter()
    # How many packages use a symbol at all, which is a better popularity
    # signal than raw count: one package calling something 400 times
    # should not outrank 40 packages calling it once.
    package_counts: Counter[str] = Counter()
    scanned = missing = empty = 0
    files = 0

    for package in queryset:
        path = checkout_path(package)
        if not (path / ".git").is_dir():
            missing += 1
            continue

        result = scan_checkout(path, tuple(scan_packages))
        scanned += 1
        files += result.files_scanned

        if not result.usage:
            empty += 1
            continue

        overall.update(result.usage)
        package_counts.update(result.usage.keys())

        if not totals_only:
            rprint(
                f"[bold]{package.slug}[/bold] "
                f"[dim]{result.symbols:,} symbols, {result.total:,} uses, "
                f"{result.files_scanned:,} files[/dim]"
            )
            for symbol, count in result.usage.most_common(top):
                rprint(f"  {count:>6,}  {symbol}")

    rprint(
        f"\nscanned {scanned:,}  missing checkout {missing:,}  "
        f"no usage {empty:,}  files {files:,}"
    )

    if overall:
        rprint(f"\n[bold]Most widely used, across {scanned:,} packages[/bold]")
        for symbol, n in package_counts.most_common(top):
            rprint(f"  {n:>6,} packages  {overall[symbol]:>8,} uses  {symbol}")

    rprint(f"[dim]checkouts in {settings.PACKAGE_REPO_ROOT}[/dim]")
