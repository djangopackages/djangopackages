from collections import Counter

import djclick as click
from rich.console import Console
from rich.table import Table

from grid.ai import (
    MIN_CONFIDENCE,
    ElementVerdict,
    build_agent,
    confidence_of,
    describe_element,
    format_answer,
    is_confident,
    legend_support,
    truncate,
)
from grid.models import Element, Grid
from package.models import Package

console = Console()

# Levels that mean the cell tells a reader nothing.
EMPTY_ANSWERS = {"unknown"}


def elements(limit, slug, feature, include_archived):
    rows = Element.objects.select_related(
        "grid_package__grid", "grid_package__package", "feature"
    ).order_by(
        "grid_package__grid__slug", "feature__title", "grid_package__package__slug"
    )

    if not include_archived:
        rows = rows.filter(grid_package__package__in=Package.objects.active())

    if slug:
        rows = rows.filter(grid_package__grid__slug=slug)
    if feature:
        rows = rows.filter(feature__title__icontains=feature)

    if limit:
        rows = rows[:limit]

    return rows


@click.command()
@click.option("--limit", default=20, type=int, help="Cells to read. 0 means all.")
@click.option("--slug", default=None, help="Only read one grid, by slug.")
@click.option("--feature", default=None, help="Only features matching this text.")
@click.option(
    "--all-cells",
    is_flag=True,
    help="Send even the obvious legend cells to Jev instead of mapping locally.",
)
@click.option(
    "--include-archived",
    is_flag=True,
    help="Read cells for archived and deprecated packages too. Skipped by default.",
)
@click.option(
    "--only-problems", is_flag=True, help="Print only placeholders and unknowns."
)
@click.option(
    "--min-confidence",
    default=MIN_CONFIDENCE,
    type=float,
    help=f"Bar for counting a verdict. Default {MIN_CONFIDENCE}.",
)
def command(
    limit, slug, feature, all_cells, include_archived, only_problems, min_confidence
):
    """
    Read each grid cell back as one of five support levels.

    The cells are free text with no convention beyond a loose icon legend, so
    the same answer shows up as "yes", "+", "Yes, since 2.0", and a sentence.
    This classifies each one as supported, partial, not_supported, unknown, or
    not_applicable, and flags the cells that are filler rather than an answer.

    Cells for archived and deprecated packages are skipped. Reading a dead
    package's row buys nothing. --include-archived puts them back.

    Cells that are already a legend token ("yes", "no", "+", "-") are mapped
    locally and cost nothing. Pass --all-cells to send those to Jev too.

    Answers below the confidence bar are dimmed and counted as unsure rather
    than for or against. Nothing is written to the database. Reads twenty
    cells unless told otherwise, since each one Jev sees costs an API call.
    """
    if slug and not Grid.objects.filter(slug=slug).exists():
        console.print(f"[red]No grid with slug {slug!r}.[/red]")
        raise SystemExit(1)

    rows = elements(limit, slug, feature, include_archived)
    total = rows.count() if hasattr(rows, "count") else len(rows)

    if not total:
        console.print("[yellow]No grid cells matched.[/yellow]")
        return

    console.print(f"Reading [bold]{total}[/bold] grid cell(s)\n")

    agent = build_agent(ElementVerdict)
    read = []

    for row in rows:
        shortcut = None if all_cells else legend_support(row.text)

        if shortcut is not None:
            read.append((row, shortcut, True, {}, not (row.text or "").strip()))
            continue

        text = describe_element(
            row.grid_package.grid, row.grid_package.package, row.feature, row.text
        )

        try:
            result = agent.run_sync(text)
        except Exception as exc:
            console.print(
                f"[red]{row.grid_package.grid.slug}/{row.grid_package.package.slug}"
                f"/{row.feature.title}: {type(exc).__name__}: {exc}[/red]"
            )
            continue

        confidence = confidence_of(result)
        read.append(
            (
                row,
                result.output.support,
                False,
                confidence,
                result.output.is_placeholder,
            )
        )

    if not read:
        console.print("[red]Nothing read.[/red]")
        return

    table = Table(title="Grid cells, classified")
    table.add_column("Grid")
    table.add_column("Package")
    table.add_column("Feature")
    table.add_column("Cell")
    table.add_column("Reads as")
    table.add_column("From")

    tally = Counter()
    placeholders = []
    unsure = []

    for row, support, from_legend, confidence, is_placeholder in read:
        sure = from_legend or is_confident(confidence, "support", min_confidence)
        sure_placeholder = from_legend or is_confident(
            confidence, "is_placeholder", min_confidence
        )

        if sure:
            tally[support] += 1
        else:
            unsure.append(row)

        flagged = (sure_placeholder and is_placeholder) or (
            sure and support in EMPTY_ANSWERS
        )
        if flagged:
            placeholders.append((row, support))

        if only_problems and not flagged:
            continue

        reads_as = (
            f"{support}"
            if from_legend
            else format_answer(support, confidence, "support", min_confidence)
        )

        table.add_row(
            row.grid_package.grid.slug,
            row.grid_package.package.slug,
            truncate(row.feature.title, 30),
            truncate(row.text, 40) or "[dim](empty)[/dim]",
            f"[red]{reads_as}[/red]" if flagged else reads_as,
            "legend" if from_legend else "jev",
        )

    console.print()
    console.print(table)

    spread = ", ".join(f"{level}: {count}" for level, count in tally.most_common())
    console.print(
        f"\nread {len(read)} | {spread or 'nothing counted'} "
        f"| says nothing: {len(placeholders)} | unsure: {len(unsure)} "
        f"| confidence bar: {min_confidence}"
    )

    if placeholders:
        console.print("\n[bold]Cells that answer nothing:[/bold]")
        for row, support in placeholders:
            console.print(
                f"  {row.grid_package.grid.slug} / "
                f"{row.grid_package.package.slug} / {row.feature.title}: "
                f"{truncate(row.text, 60) or '(empty)'}"
            )
