from collections import defaultdict

import djclick as click
from rich.console import Console
from rich.table import Table

from grid.ai import (
    MIN_CONFIDENCE,
    PackageVerdict,
    approve_each,
    build_agent,
    confidence_of,
    describe_package_in_grid,
    format_answer,
    is_confident,
    truncate,
)
from grid.models import Grid, GridPackage
from package.models import Category, Package

console = Console()


def grid_packages(limit, slug, category, include_archived):
    rows = GridPackage.objects.select_related(
        "grid", "package", "package__category"
    ).order_by("package__slug", "grid__slug")

    if not include_archived:
        rows = rows.filter(package__in=Package.objects.active())

    if slug:
        rows = rows.filter(grid__slug=slug)
    if category:
        rows = rows.filter(package__category__slug=category)

    if category:
        # Sweeping a category asks about packages, not placements, and the
        # installation type does not change with the grid. One row per
        # package, so a package on six grids costs one call rather than six.
        rows = dedupe_by_package(rows)

    if limit:
        rows = rows[:limit]

    return rows


def dedupe_by_package(rows):
    seen = set()
    kept = []
    for row in rows:
        if row.package_id in seen:
            continue
        seen.add(row.package_id)
        kept.append(row)
    return kept


@click.command()
@click.option(
    "--limit", default=10, type=int, help="Packages to review. 0 means all of them."
)
@click.option("--slug", default=None, help="Only review one grid, by slug.")
@click.option(
    "--category",
    default=None,
    help="Only packages filed under this installation type, e.g. 'other'.",
)
@click.option("--only-problems", is_flag=True, help="Print only the flagged rows.")
@click.option(
    "--include-archived",
    is_flag=True,
    help="Review archived and deprecated packages too. They are skipped by default.",
)
@click.option(
    "--min-confidence",
    default=MIN_CONFIDENCE,
    type=float,
    help=f"Bar for acting on a verdict. Default {MIN_CONFIDENCE}.",
)
@click.option(
    "--apply-moves",
    is_flag=True,
    help="Offer to refile each confidently miscategorised package. Writes.",
)
@click.option(
    "--apply-removals",
    is_flag=True,
    help="Offer to drop each package Jev says is off-topic for its grid. Writes.",
)
@click.option(
    "--yes",
    "assume_yes",
    is_flag=True,
    help="Answer yes to every prompt. Only means anything with an --apply flag.",
)
def command(
    limit,
    slug,
    category,
    include_archived,
    only_problems,
    min_confidence,
    apply_moves,
    apply_removals,
    assume_yes,
):
    """
    Ask Jev whether each package belongs in the grid it is listed on.

    Also asks which installation type the package looks like (apps,
    developer-tools, frameworks, other, projects, starter-projects) and
    reports it when that disagrees with the category it is filed under.

    Archived and deprecated packages are skipped. Refiling a dead package
    buys nothing, and in production 939 of the 5,836 packages are archived
    or deprecated. --include-archived puts them back.

    Pass --category other to sweep the ~680 packages sitting in "Other".
    A category sweep reviews each package once rather than once per grid it
    appears on, and the report ends with the moves grouped by destination,
    ready to work through.

    Only answers at or above the confidence bar are flagged. Anything below
    it is listed as unsure instead, so a hesitant answer never reads as a
    recommendation.

    Read-only by default. --apply-moves offers to refile each miscategorised
    package and --apply-removals offers to drop each off-topic one from its
    grid, both one at a time, showing the package's own description so the
    recommendation can be judged on something other than the label. Each
    prompt takes y, n, or q to stop. --yes answers them all.

    Reviews ten rows unless told otherwise, since each row costs one API call.
    """
    if slug and not Grid.objects.filter(slug=slug).exists():
        console.print(f"[red]No grid with slug {slug!r}.[/red]")
        raise SystemExit(1)

    if category and not Category.objects.filter(slug=category).exists():
        known = ", ".join(Category.objects.values_list("slug", flat=True))
        console.print(f"[red]No category {category!r}. Try one of: {known}.[/red]")
        raise SystemExit(1)

    if apply_removals and category:
        console.print(
            "[red]--apply-removals needs a grid to remove from, and a "
            "category sweep reviews each package once across all of them. "
            "Use --slug, or drop --category.[/red]"
        )
        raise SystemExit(1)

    if assume_yes and not (apply_moves or apply_removals):
        console.print("[yellow]--yes does nothing without an --apply flag.[/yellow]")

    rows = grid_packages(limit, slug, category, include_archived)
    # A category sweep hands back a list, so len, not .count().
    total = len(rows) if isinstance(rows, list) else rows.count()

    if not total:
        console.print("[yellow]No grid packages matched.[/yellow]")
        return

    console.print(f"Reviewing [bold]{total}[/bold] grid package(s) with Jev\n")

    agent = build_agent(PackageVerdict)
    reviewed = []

    for row in rows:
        text = describe_package_in_grid(row.grid, row.package)

        try:
            result = agent.run_sync(text)
        except Exception as exc:
            console.print(
                f"[red]{row.grid.slug}/{row.package.slug}: "
                f"{type(exc).__name__}: {exc}[/red]"
            )
            continue

        reviewed.append((row, result.output, confidence_of(result)))

    if not reviewed:
        console.print("[red]Nothing reviewed.[/red]")
        return

    # A category sweep already dropped the duplicate rows, so the grid shown
    # would be an arbitrary one of several, and "belongs in it" comes back
    # unsure almost every time. Both columns are dropped to leave room for the
    # one being swept for.
    sweeping = bool(category)

    table = Table(title="Package placement", show_lines=False)
    table.add_column("Package")
    if not sweeping:
        table.add_column("Grid")
        table.add_column("Belongs?")
    table.add_column("Filed as")
    # Wide enough that the arrow stays on the same line as the type it points to.
    table.add_column("Jev says", min_width=24)

    flagged_removals = []
    flagged_categories = []
    unsure = []

    for row, verdict, confidence in reviewed:
        current = row.package.category.slug
        disagrees = verdict.installation_type != current

        sure_on_grid = is_confident(confidence, "belongs_in_grid", min_confidence)
        sure_on_type = is_confident(confidence, "installation_type", min_confidence)

        if sure_on_grid and not verdict.belongs_in_grid:
            flagged_removals.append(row)
        if sure_on_type and disagrees:
            flagged_categories.append((row, verdict.installation_type))
        # While sweeping, "belongs in this grid" is not being reported, so it
        # should not be what makes a row unsure either.
        if sweeping:
            if not sure_on_type:
                unsure.append(row)
        elif not sure_on_grid or (disagrees and not sure_on_type):
            unsure.append(row)

        a_problem = (sure_on_grid and not verdict.belongs_in_grid) or (
            sure_on_type and disagrees
        )
        if only_problems and not a_problem:
            continue

        belongs = format_answer(
            "yes" if verdict.belongs_in_grid else "no",
            confidence,
            "belongs_in_grid",
            min_confidence,
        )
        says = format_answer(
            verdict.installation_type, confidence, "installation_type", min_confidence
        )

        # A confident mismatch is the whole point of the table, so it gets an
        # arrow and the colour, and the category it is leaving goes dim.
        filed_as = current
        if sure_on_type and disagrees:
            filed_as = f"[dim]{current}[/dim]"
            says = f"[bold yellow]-> {says}[/bold yellow]"

        cells = [row.package.slug]
        if not sweeping:
            cells += [row.grid.slug, belongs]
        cells += [filed_as, says]

        table.add_row(*cells)

    console.print()
    console.print(table)

    summary = [f"reviewed {len(reviewed)} at >={min_confidence}"]
    if not sweeping:
        summary.append(f"would remove from grid: {len(flagged_removals)}")
    summary.append(f"category disagreement: {len(flagged_categories)}")
    summary.append(f"unsure: {len(unsure)}")

    console.print("\n" + " | ".join(summary))

    if flagged_removals and apply_removals:
        apply_grid_removals(flagged_removals, assume_yes)
    elif flagged_removals:
        console.print("\n[bold]Jev would remove these from their grid:[/bold]")
        for row in flagged_removals:
            console.print(f"  {row.package.slug} -> out of {row.grid.slug}")

    if flagged_categories and apply_moves:
        apply_category_moves(flagged_categories, assume_yes)
    elif flagged_categories:
        console.print("\n[bold]Moves to make, by destination:[/bold]")
        by_destination = defaultdict(list)
        for row, suggested in flagged_categories:
            by_destination[suggested].append(row)

        for destination, moving in sorted(by_destination.items()):
            console.print(f"\n  -> {destination} ({len(moving)})")
            for row in moving:
                console.print(
                    f"     {row.package.slug} (from {row.package.category.slug})"
                )


def apply_category_moves(flagged, assume_yes):
    """Refile the approved packages. Nothing moves without a yes."""
    console.print("\n[bold]Refiling packages[/bold]")

    def describe(finding):
        row, suggested = finding
        package = row.package
        return [
            f"\n  [bold]{package.slug}[/bold]: "
            f"{package.category.slug} -> [bold yellow]{suggested}[/bold yellow]",
            f"  {truncate(package.repo_description, 160) or '(no description)'}",
            f"  {package.repo_url or '(no repo)'}",
        ]

    moved = 0
    destinations = {}

    for row, suggested in approve_each(console, flagged, assume_yes, describe):
        if suggested not in destinations:
            destinations[suggested] = Category.objects.get(slug=suggested)

        package = row.package
        package.category = destinations[suggested]
        package.save(update_fields=["category"])
        moved += 1

    console.print(f"\n[bold]{moved} package(s) refiled.[/bold]")


def apply_grid_removals(flagged, assume_yes):
    """Drop the approved packages from their grid. The package itself stays."""
    console.print("\n[bold]Removing packages from grids[/bold]")

    def describe(row):
        return [
            f"\n  [bold]{row.package.slug}[/bold] out of "
            f"[bold yellow]{row.grid.slug}[/bold yellow]",
            f"  grid: {truncate(row.grid.description, 120) or '(no description)'}",
            f"  package: "
            f"{truncate(row.package.repo_description, 160) or '(no description)'}",
        ]

    removed = 0

    for row in approve_each(console, flagged, assume_yes, describe):
        GridPackage.objects.filter(pk=row.pk).delete()
        removed += 1

    console.print(
        f"\n[bold]{removed} package(s) removed from their grid.[/bold] "
        "The packages themselves are untouched."
    )
