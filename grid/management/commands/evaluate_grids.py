import djclick as click
from django.db.models import Count
from rich.console import Console
from rich.table import Table

from grid.ai import (
    GRID_CRITERIA,
    MIN_CONFIDENCE,
    GridVerdict,
    Quality,
    build_agent,
    confidence_of,
    describe_grid,
)
from grid.models import Feature, Grid

console = Console()

# A criterion at or below this level, answered confidently, means the grid
# needs attention.
NEEDS_WORK_AT_OR_BELOW = Quality.WEAK


def grid_rows(limit, slug, min_packages):
    grids = Grid.objects.annotate(package_count=Count("packages", distinct=True))

    if slug:
        grids = grids.filter(slug=slug)
    if min_packages is not None:
        grids = grids.filter(package_count__gte=min_packages)

    grids = grids.order_by("-package_count", "slug")

    if limit:
        grids = grids[:limit]

    return grids


def cell(verdict, confidence, field, threshold):
    level = Quality(getattr(verdict, field))
    score = confidence.get(field)

    if score is None:
        return f"[dim]{level.name} (?)[/dim]"
    if score < threshold:
        return f"[dim]{level.name} ({score:.2f})[/dim]"
    if level <= NEEDS_WORK_AT_OR_BELOW:
        return f"[red]{level.name}[/red] ({score:.2f})"
    return f"{level.name} ({score:.2f})"


@click.command()
@click.option("--limit", default=5, type=int, help="Grids to review. 0 means all.")
@click.option("--slug", default=None, help="Review a single grid by slug.")
@click.option("--min-packages", default=None, type=int, help="Skip smaller grids.")
@click.option(
    "--min-confidence",
    default=MIN_CONFIDENCE,
    type=float,
    help=f"Bar for counting a verdict. Default {MIN_CONFIDENCE}.",
)
def command(limit, slug, min_packages, min_confidence):
    """
    Score every comparison grid with Jev and print a report, worst first.

    Three rubrics per grid: whether the packages share one focused topic,
    whether the title and description are specific, and whether there is
    enough there to work as a comparison.

    Answers below the confidence bar are dimmed and do not count toward the
    verdict, so a grid is only called out when Jev is actually sure. A grid
    needs work when a criterion comes back WEAK or UNUSABLE confidently.

    Nothing is written to the database. Reviews five grids unless told
    otherwise, since each grid costs one API call.
    """
    grids = grid_rows(limit, slug, min_packages)
    total = grids.count() if hasattr(grids, "count") else len(grids)

    if not total:
        console.print("[yellow]No grids matched.[/yellow]")
        return

    console.print(f"Reviewing [bold]{total}[/bold] grid(s) with Jev\n")

    agent = build_agent(GridVerdict)
    results = []

    for grid in grids:
        packages = list(grid.packages.select_related("category").all())
        features = list(
            Feature.objects.filter(grid=grid).values_list("title", flat=True)
        )

        try:
            result = agent.run_sync(describe_grid(grid, packages, features))
        except Exception as exc:
            console.print(f"[red]{grid.slug}: {type(exc).__name__}: {exc}[/red]")
            continue

        results.append((grid, len(packages), result.output, confidence_of(result)))
        console.print(f"  reviewed {grid.slug}")

    if not results:
        console.print("[red]Nothing reviewed.[/red]")
        return

    def failings(verdict, confidence):
        """Criteria answered confidently and badly."""
        return [
            field
            for field in GRID_CRITERIA
            if confidence.get(field, 0.0) >= min_confidence
            and Quality(getattr(verdict, field)) <= NEEDS_WORK_AT_OR_BELOW
        ]

    def sort_key(row):
        _, _, verdict, confidence = row
        counted = [
            Quality(getattr(verdict, field))
            for field in GRID_CRITERIA
            if confidence.get(field, 0.0) >= min_confidence
        ]
        return (
            -len(failings(verdict, confidence)),
            sum(counted) if counted else 99,
        )

    results.sort(key=sort_key)

    table = Table(title="Grid quality, worst first")
    table.add_column("Grid")
    table.add_column("Pkgs", justify="right")
    table.add_column("Topic")
    table.add_column("Title/desc")
    table.add_column("Comparable")
    table.add_column("Verdict")

    needs_work = []

    for grid, package_count, verdict, confidence in results:
        bad = failings(verdict, confidence)
        counted = sum(
            1 for field in GRID_CRITERIA if confidence.get(field, 0.0) >= min_confidence
        )

        if bad:
            needs_work.append((grid, bad))
            summary = f"[red]needs work[/red] ({len(bad)})"
        elif counted:
            summary = "ok"
        else:
            summary = "[dim]unsure[/dim]"

        table.add_row(
            grid.slug,
            str(package_count),
            cell(verdict, confidence, "topic_coherence", min_confidence),
            cell(verdict, confidence, "title_and_description", min_confidence),
            cell(verdict, confidence, "useful_as_comparison", min_confidence),
            summary,
        )

    console.print()
    console.print(table)
    console.print(
        f"\nreviewed {len(results)} | needs work: {len(needs_work)} "
        f"| confidence bar: {min_confidence}"
    )

    for grid, bad in needs_work:
        console.print(f"  {grid.slug}: " + ", ".join(bad))
