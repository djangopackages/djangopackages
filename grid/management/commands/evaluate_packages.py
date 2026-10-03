"""Lives here rather than under package/ because it needs grid.ai, and grid
already imports from package. Moving it would point the dependency both ways.
"""

from collections import defaultdict

import djclick as click
from rich.console import Console
from rich.table import Table

from grid.ai import (
    MIN_CONFIDENCE,
    PackageOnlyVerdict,
    build_agent,
    confidence_of,
    describe_package,
    format_answer,
    is_confident,
    truncate,
)
from package.models import Category, Package

console = Console()


def off_grid_packages(limit, category):
    packages = (
        Package.objects.select_related("category")
        .filter(gridpackage__isnull=True)
        .order_by("slug")
    )

    if category:
        packages = packages.filter(category__slug=category)

    if limit:
        packages = packages[:limit]

    return packages


@click.command()
@click.option("--limit", default=10, type=int, help="Packages to review. 0 means all.")
@click.option(
    "--category",
    default=None,
    help="Only packages filed under this installation type, e.g. 'other'.",
)
@click.option(
    "--only-problems",
    is_flag=True,
    help="Print only the moves and the packages missing a description.",
)
@click.option(
    "--min-confidence",
    default=MIN_CONFIDENCE,
    type=float,
    help=f"Bar for acting on a verdict. Default {MIN_CONFIDENCE}.",
)
def command(limit, category, only_problems, min_confidence):
    """
    Review the packages that are on no comparison grid.

    evaluate_grid_packages walks grid rows, so a package nobody has added to
    a grid is invisible to it. Those are the ones most likely to be sitting
    in the wrong category, because nobody has had reason to look at them.

    Two questions per package: which installation type it looks like, and
    whether its description says enough to tell. The second matters here.
    A package is usually untriaged for want of a description, and "there is
    nothing to go on" needs a different fix from "this is filed wrong".

    Answers below the confidence bar are reported as unsure rather than
    counted. Nothing is written to the database. Reviews ten packages unless
    told otherwise, since each one costs an API call.
    """
    if category and not Category.objects.filter(slug=category).exists():
        known = ", ".join(Category.objects.values_list("slug", flat=True))
        console.print(f"[red]No category {category!r}. Try one of: {known}.[/red]")
        raise SystemExit(1)

    packages = off_grid_packages(limit, category)
    total = packages.count()

    if not total:
        console.print("[yellow]No off-grid packages matched.[/yellow]")
        return

    console.print(f"Reviewing [bold]{total}[/bold] off-grid package(s) with Jev\n")

    agent = build_agent(PackageOnlyVerdict)
    reviewed = []

    for package in packages:
        try:
            result = agent.run_sync(describe_package(package))
        except Exception as exc:
            console.print(f"[red]{package.slug}: {type(exc).__name__}: {exc}[/red]")
            continue

        reviewed.append((package, result.output, confidence_of(result)))

    if not reviewed:
        console.print("[red]Nothing reviewed.[/red]")
        return

    table = Table(title="Off-grid packages")
    table.add_column("Package")
    table.add_column("Filed as")
    table.add_column("Jev says")
    table.add_column("Description")

    moves = []
    needs_description = []
    unsure = []

    for package, verdict, confidence in reviewed:
        current = package.category.slug
        disagrees = verdict.installation_type != current

        sure_on_type = is_confident(confidence, "installation_type", min_confidence)
        sure_on_description = is_confident(
            confidence, "description_is_usable", min_confidence
        )

        if sure_on_description and not verdict.description_is_usable:
            needs_description.append(package)
        if sure_on_type and disagrees:
            moves.append((package, verdict.installation_type))
        if not sure_on_type:
            unsure.append(package)

        a_problem = (sure_on_type and disagrees) or (
            sure_on_description and not verdict.description_is_usable
        )
        if only_problems and not a_problem:
            continue

        table.add_row(
            package.slug,
            current,
            format_answer(
                verdict.installation_type,
                confidence,
                "installation_type",
                min_confidence,
            ),
            format_answer(
                "usable" if verdict.description_is_usable else "too thin",
                confidence,
                "description_is_usable",
                min_confidence,
            ),
        )

    console.print()
    console.print(table)
    console.print(
        f"\nreviewed {len(reviewed)} at >={min_confidence} | "
        f"moves: {len(moves)} | needs a description: {len(needs_description)} "
        f"| unsure: {len(unsure)}"
    )

    if moves:
        console.print("\n[bold]Moves to make, by destination:[/bold]")
        by_destination = defaultdict(list)
        for package, suggested in moves:
            by_destination[suggested].append(package)

        for destination, moving in sorted(by_destination.items()):
            console.print(f"\n  -> {destination} ({len(moving)})")
            for package in moving:
                console.print(f"     {package.slug} (from {package.category.slug})")

    if needs_description:
        console.print("\n[bold]Fix the description before classifying:[/bold]")
        for package in needs_description:
            console.print(
                f"  {package.slug}: {truncate(package.repo_description, 60) or '(none)'}"
            )
