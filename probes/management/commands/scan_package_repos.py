from __future__ import annotations

from collections import Counter

import djclick as click
from django.conf import settings
from rich import print as rprint

from package.models import Package
from probes import stats as probe_stats
from probes.checkouts import scannable_packages
from probes.pipeline import libraries_to_scan, scan_package


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
    "--force",
    is_flag=True,
    help=(
        "Rescan checkouts whose commit has not changed since the last scan, "
        "as after upgrading django-probe"
    ),
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
def command(
    slugs: tuple[str, ...],
    limit: int | None,
    scan_packages: tuple[str, ...],
    top: int,
    totals_only: bool,
    min_score: int,
    dry_run: bool,
    force: bool,
):
    """Count which Django APIs the checked out packages actually use.

    Reads the checkouts that sync_package_repos produced; it never
    touches the network. Packages with no checkout are counted as
    missing rather than treated as using nothing.

    A checkout still on the commit its profile was read from, scanned
    for the same libraries, is skipped: parsing it again would only
    write back what is already stored. Skipped packages are left out of
    the roll-up printed at the end, which covers what this run read.
    Pass --force to read everything.
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
    # The stored profile is what decides whether a checkout has changed.
    queryset = queryset.select_related("probe_profile")
    if limit:
        queryset = queryset[:limit]

    scan_packages = libraries_to_scan(scan_packages)

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
    scanned = missing = empty = unchanged = 0
    files = 0

    for package in queryset:
        status, result = scan_package(
            package, scan_packages, force=force, save=not dry_run
        )
        if status == "missing":
            missing += 1
            continue
        if status == "unchanged":
            unchanged += 1
            continue

        scanned += 1
        files += result.files_scanned

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

    if scanned and not dry_run:
        probe_stats.invalidate()

    rprint(
        f"\nscanned {scanned:,}  unchanged {unchanged:,}  "
        f"missing checkout {missing:,}  no usage {empty:,}  files {files:,}"
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
