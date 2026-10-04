import djclick as click
from django.db.models import Count
from rich.console import Console
from rich.table import Table

from grid.ai import (
    GRID_CRITERIA,
    GRID_REMOVAL,
    MIN_CONFIDENCE,
    GridVerdict,
    Quality,
    approve_each,
    build_agent,
    confidence_of,
    describe_grid,
    format_answer,
    is_confident,
    truncate,
)
from grid.models import Element, Feature, Grid

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
@click.option(
    "--apply-unapprove",
    is_flag=True,
    help="Offer to hide each grid listed for removal. Reversible. Writes.",
)
@click.option(
    "--apply-delete",
    is_flag=True,
    help="Offer to delete each grid listed for removal, and its features and "
    "cells with it. Not reversible, and never takes --yes.",
)
@click.option(
    "--yes",
    "assume_yes",
    is_flag=True,
    help="Answer yes to every prompt. Refused with --apply-delete.",
)
def command(
    limit,
    slug,
    min_packages,
    min_confidence,
    apply_unapprove,
    apply_delete,
    assume_yes,
):
    """
    Score every comparison grid with Jev and print a report, worst first.

    Three rubrics per grid: whether the packages share one focused topic,
    whether the title and description are specific, and whether there is
    enough there to work as a comparison. Jev is also asked whether a field
    of competing packages exists for the topic at all, which is the removal
    question editing cannot fix.

    A grid with fewer than two packages is listed for removal on the count
    alone, without waiting for the model to agree.

    Answers below the confidence bar are dimmed and do not count toward the
    verdict, so a grid is only called out when Jev is actually sure. A grid
    needs work when a criterion comes back WEAK or UNUSABLE confidently, and
    is listed for removal when it is empty or Jev confidently says there is
    no field of packages behind the topic.

    Read-only by default. Two ways to act on the removal list, one at a
    time, each showing the grid's own title, description, and contents:

    --apply-unapprove hides the grid by clearing is_approved. The grid, its
    features, and its cells all survive, and switching it back is one click
    in the admin. This is the one to reach for.

    --apply-delete deletes the grid outright, taking its features and its
    cells with it. The prompt shows how much goes, and the flag does not
    accept --yes, because the whole point of it is that someone looked.

    Reviews five grids unless told otherwise, since each costs one API call.
    """
    if apply_unapprove and apply_delete:
        console.print("[red]Pick one of --apply-unapprove and --apply-delete.[/red]")
        raise SystemExit(1)

    if apply_delete and assume_yes:
        console.print(
            "[red]--yes is not accepted with --apply-delete. Deleting a grid "
            "takes its features and cells with it, so each one is confirmed "
            "on its own.[/red]"
        )
        raise SystemExit(1)

    if assume_yes and not apply_unapprove:
        console.print("[yellow]--yes does nothing without an --apply flag.[/yellow]")

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

    def removal_reason(package_count, verdict, confidence):
        """Empty is a fact we can see; the rest needs a confident answer."""
        if package_count < 2:
            return f"only {package_count} package(s)"
        if not verdict.topic_is_worth_a_grid and is_confident(
            confidence, GRID_REMOVAL, min_confidence
        ):
            return "no field of packages for this topic"
        return None

    def sort_key(row):
        _, package_count, verdict, confidence = row
        counted = [
            Quality(getattr(verdict, field))
            for field in GRID_CRITERIA
            if confidence.get(field, 0.0) >= min_confidence
        ]
        return (
            removal_reason(package_count, verdict, confidence) is None,
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
    table.add_column("Remove?")
    table.add_column("Verdict")

    needs_work = []
    removals = []

    for grid, package_count, verdict, confidence in results:
        bad = failings(verdict, confidence)
        counted = sum(
            1 for field in GRID_CRITERIA if confidence.get(field, 0.0) >= min_confidence
        )
        remove = removal_reason(package_count, verdict, confidence)

        if remove:
            removals.append((grid, remove))
            summary = "[red]remove[/red]"
        elif bad:
            summary = f"[red]needs work[/red] ({len(bad)})"
        elif counted:
            summary = "ok"
        else:
            summary = "[dim]unsure[/dim]"

        # A grid slated for deletion does not also need a better description.
        if bad and not remove:
            needs_work.append((grid, bad))

        table.add_row(
            grid.slug,
            str(package_count),
            cell(verdict, confidence, "topic_coherence", min_confidence),
            cell(verdict, confidence, "title_and_description", min_confidence),
            cell(verdict, confidence, "useful_as_comparison", min_confidence),
            format_answer(
                "no" if verdict.topic_is_worth_a_grid else "yes",
                confidence,
                GRID_REMOVAL,
                min_confidence,
            ),
            summary,
        )

    console.print()
    console.print(table)
    console.print(
        f"\nreviewed {len(results)} | needs work: {len(needs_work)} "
        f"| would remove: {len(removals)} | confidence bar: {min_confidence}"
    )

    if removals and apply_unapprove:
        apply_unapproval(removals, assume_yes)
    elif removals and apply_delete:
        apply_deletion(removals)
    elif removals:
        console.print("\n[bold]Grids to remove:[/bold]")
        for grid, reason in removals:
            console.print(f"  {grid.slug}: {reason}")

    if needs_work:
        console.print("\n[bold]Grids to fix:[/bold]")
        for grid, bad in needs_work:
            console.print(f"  {grid.slug}: " + ", ".join(bad))


def contents_of(grid):
    """What a grid is carrying, so a prompt can say what goes with it."""
    return {
        "packages": grid.packages.count(),
        "features": Feature.objects.filter(grid=grid).count(),
        "cells": Element.objects.filter(feature__grid=grid).count(),
    }


def describe_for_prompt(finding, verb):
    grid, reason = finding
    counts = contents_of(grid)
    return [
        f"\n  [bold]{grid.slug}[/bold]: {verb} ([yellow]{reason}[/yellow])",
        f"  {grid.title}",
        f"  {truncate(grid.description, 160) or '(no description)'}",
        f"  {counts['packages']} package(s), {counts['features']} feature(s), "
        f"{counts['cells']} cell(s)",
    ]


def apply_unapproval(removals, assume_yes):
    """Hide the approved grids. Everything they hold survives."""
    console.print("\n[bold]Hiding grids[/bold]")

    pending = [(grid, reason) for grid, reason in removals if grid.is_approved]
    already = len(removals) - len(pending)

    if already:
        console.print(f"  [dim]{already} already hidden, skipped[/dim]")

    hidden = 0

    for grid, _ in approve_each(
        console,
        pending,
        assume_yes,
        lambda finding: describe_for_prompt(finding, "hide"),
    ):
        grid.is_approved = False
        grid.save(update_fields=["is_approved"])
        hidden += 1

    console.print(
        f"\n[bold]{hidden} grid(s) hidden.[/bold] "
        "Their packages, features, and cells are untouched."
    )


def apply_deletion(removals):
    """Delete the grids outright. Features and cells go with them."""
    console.print("\n[bold]Deleting grids[/bold]")
    console.print("  [red]This cannot be undone.[/red]")

    deleted = 0
    lost = {"features": 0, "cells": 0}

    for grid, _ in approve_each(
        console,
        removals,
        False,
        lambda finding: describe_for_prompt(finding, "[red]DELETE[/red]"),
    ):
        counts = contents_of(grid)
        lost["features"] += counts["features"]
        lost["cells"] += counts["cells"]
        grid.delete()
        deleted += 1

    console.print(
        f"\n[bold]{deleted} grid(s) deleted[/bold], taking "
        f"{lost['features']} feature(s) and {lost['cells']} cell(s) with them. "
        "The packages themselves are untouched."
    )
