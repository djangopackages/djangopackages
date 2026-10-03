import djclick as click
from rich.console import Console
from rich.table import Table

from grid.ai import (
    MIN_CONFIDENCE,
    PackageVerdict,
    build_agent,
    confidence_of,
    describe_package_in_grid,
    format_answer,
    is_confident,
)
from grid.models import Grid, GridPackage

console = Console()


def grid_packages(limit, slug):
    rows = GridPackage.objects.select_related(
        "grid", "package", "package__category"
    ).order_by("grid__slug", "package__slug")

    if slug:
        rows = rows.filter(grid__slug=slug)

    if limit:
        rows = rows[:limit]

    return rows


@click.command()
@click.option(
    "--limit", default=10, type=int, help="Packages to review. 0 means all of them."
)
@click.option("--slug", default=None, help="Only review one grid, by slug.")
@click.option("--only-problems", is_flag=True, help="Print only the flagged rows.")
@click.option(
    "--min-confidence",
    default=MIN_CONFIDENCE,
    type=float,
    help=f"Bar for acting on a verdict. Default {MIN_CONFIDENCE}.",
)
def command(limit, slug, only_problems, min_confidence):
    """
    Ask Jev whether each package belongs in the grid it is listed on.

    Also asks which installation type the package looks like (apps,
    frameworks, other, projects, starter-projects) and reports it when that
    disagrees with the category it is filed under. Useful against the ~815
    packages sitting in "Other".

    Only answers at or above the confidence bar are flagged. Anything below
    it is listed as unsure instead, so a hesitant answer never reads as a
    recommendation.

    Nothing is written to the database. Reviews ten rows unless told
    otherwise, since each row costs one API call.
    """
    if slug and not Grid.objects.filter(slug=slug).exists():
        console.print(f"[red]No grid with slug {slug!r}.[/red]")
        raise SystemExit(1)

    rows = grid_packages(limit, slug)
    total = rows.count() if hasattr(rows, "count") else len(rows)

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

    table = Table(title="Package placement", show_lines=False)
    table.add_column("Grid")
    table.add_column("Package")
    table.add_column("Belongs?")
    table.add_column("Filed as")
    table.add_column("Jev says")

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
        if not sure_on_grid or (disagrees and not sure_on_type):
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

        table.add_row(
            row.grid.slug,
            row.package.slug,
            belongs,
            current,
            says,
        )

    console.print()
    console.print(table)

    console.print(
        f"\nreviewed {len(reviewed)} at >={min_confidence} | "
        f"would remove from grid: {len(flagged_removals)} | "
        f"category disagreement: {len(flagged_categories)} | "
        f"unsure: {len(unsure)}"
    )

    if flagged_removals:
        console.print("\n[bold]Jev would remove these from their grid:[/bold]")
        for row in flagged_removals:
            console.print(f"  {row.grid.slug} <- {row.package.slug}")

    if flagged_categories:
        console.print("\n[bold]Category disagreements:[/bold]")
        for row, suggested in flagged_categories:
            console.print(
                f"  {row.package.slug}: filed as "
                f"{row.package.category.slug}, Jev says {suggested}"
            )
