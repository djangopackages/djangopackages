from __future__ import annotations

from collections import Counter

import djclick as click
from django.conf import settings
from rich import print as rprint

from django.utils.timezone import now

from package.models import Package
from probes.models import Library, PackageProbe
from probes.checkouts import (
    checkout_commit,
    checkout_path,
    scan_checkout,
    scannable_packages,
)


@click.command()
@click.option("--slug", "slugs", multiple=True, help="Specific package slug(s)")
@click.option("--limit", default=None, type=int, help="Maximum packages to scan")
@click.option(
    "--package",
    "scan_packages",
    multiple=True,
    default=(),
    help=(
        "Top-level import name(s) to count. Defaults to the libraries "
        "toggled on in the Library table, or django if none are"
    ),
)
@click.option(
    "--top", default=20, type=int, help="Symbols to show per package (default: 20)"
)
@click.option(
    "--totals-only", is_flag=True, help="Only print the roll-up across all packages"
)
@click.option("--dry-run", is_flag=True, help="Report without saving profiles")
@click.option(
    "--min-score",
    default=0,
    type=int,
    help=(
        "Lowest package score to include. Below zero means roughly thirty "
        "months without a commit; pass -500 to reach those too (default: 0)"
    ),
)
def command(
    slugs: tuple[str, ...],
    limit: int | None,
    scan_packages: tuple[str, ...],
    top: int,
    totals_only: bool,
    min_score: int,
    dry_run: bool,
):
    """Count which Django APIs the checked out packages actually use.

    Reads the checkouts that sync_package_repos produced; it never
    touches the network. Packages with no checkout are counted as
    missing rather than treated as using nothing.
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
    if limit:
        queryset = queryset[:limit]

    # An explicit --package wins; otherwise the libraries someone has
    # toggled on, which is how this grows without a code change. Django
    # is the fallback so a fresh install still scans something.
    scan_packages = tuple(scan_packages) or Library.scan_for() or ("django",)

    overall: Counter[str] = Counter()
    # How many packages use a symbol at all, which is a better popularity
    # signal than raw count: one package calling something 400 times
    # should not outrank 40 packages calling it once.
    package_counts: Counter[str] = Counter()
    pattern_packages: Counter[str] = Counter()
    pattern_hits: Counter[str] = Counter()
    library_packages: Counter[str] = Counter()
    library_uses: Counter[str] = Counter()
    settings_packages: Counter[str] = Counter()
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

        if not dry_run:
            # Sorted most used first, since the list keeps its order and
            # the first thing anyone wants is the top of it.
            symbols = [
                {
                    "symbol": symbol,
                    "count": count,
                    "library": result.library_of(symbol),
                }
                for symbol, count in result.usage.most_common()
            ]
            patterns = [
                {"pattern": pattern, "count": count}
                for pattern, count in result.patterns.most_common()
            ]
            PackageProbe.objects.update_or_create(
                package=package,
                defaults={
                    "symbols": symbols,
                    "patterns": patterns,
                    "libraries": list(result.libraries),
                    "files_scanned": result.files_scanned,
                    "files_skipped": result.files_skipped,
                    "commit": checkout_commit(path),
                    "scanned_at": now(),
                },
            )

        library_uses.update(result.by_library)
        library_packages.update(result.by_library.keys())
        pattern_packages.update(result.patterns.keys())
        pattern_hits.update(result.patterns)
        settings_packages.update(result.settings_used.keys())

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
            if result.patterns:
                hits = ", ".join(
                    f"{pattern.removeprefix('probe:')} {count}"
                    for pattern, count in result.patterns.most_common()
                )
                rprint(f"  [dim]patterns: {hits}[/dim]")

    rprint(
        f"\nscanned {scanned:,}  missing checkout {missing:,}  "
        f"no usage {empty:,}  files {files:,}"
        + ("  [dim](dry run, nothing saved)[/dim]" if dry_run else "")
    )

    if overall:
        rprint(f"\n[bold]Most widely used, across {scanned:,} packages[/bold]")
        for symbol, n in package_counts.most_common(top):
            rprint(f"  {n:>6,} packages  {overall[symbol]:>8,} uses  {symbol}")

    if library_packages:
        rprint(f"\n[bold]Libraries, of {', '.join(scan_packages)}[/bold]")
        for library, n in library_packages.most_common():
            rprint(f"  {n:>6,} packages  {library_uses[library]:>8,} uses  {library}")

    if pattern_packages:
        rprint("\n[bold]Patterns[/bold]")
        for pattern, n in pattern_packages.most_common():
            rprint(f"  {n:>6,} packages  {pattern_hits[pattern]:>8,} hits  {pattern}")

    if settings_packages:
        rprint(f"\n[bold]Settings read, {len(settings_packages):,} distinct[/bold]")
        for name, n in settings_packages.most_common(top):
            rprint(f"  {n:>6,} packages  {name}")

    rprint(f"[dim]checkouts in {settings.PACKAGE_REPO_ROOT}[/dim]")
