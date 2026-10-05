"""Refile packages using the grids they are already on.

Lives here rather than under package/ for the same reason evaluate_packages
does: it needs grid membership, and grid already imports from package.

Nothing here asks a model anything. The grids are the evidence. A grid is a
topic somebody curated by hand, so a package sitting on "Cookiecutters" has
already been told what it is; the category field just never caught up. See
issue #1135 for the counts behind the map below.
"""

from collections import defaultdict

import djclick as click
from rich.console import Console
from rich.table import Table

from grid.ai import approve_each, truncate
from grid.models import GridPackage
from package.models import Category, Package

console = Console()

# Grid slug -> the category a package on it almost certainly belongs in.
#
# Only grids where "Other" was the majority or near-majority of the members
# are listed, because those are the ones where the category field is clearly
# the thing that is wrong. Counts are the packages filed under "other" on
# each grid when this was measured against production, out of the 815 in
# "Other" at the time:
#
#   cookiecutters      29/41   project-templates  26/39   bootstraps  18/32
#   developer-tools    39/134  testing            32/78   linters      9/9
#   template-linters    5/5    documentation       4/5    test_clients 3/5
#
# Deployment was held back from that first pass to see how the other two
# landed. Measured again after they did: deployment 23/49, buildout 7/7,
# webserver 5/9, out of the 680 left in "Other".
GRID_CATEGORY_MAP = {
    "bootstraps": "starter-projects",
    "cookiecutters": "starter-projects",
    "project-templates": "starter-projects",
    "developer-tools": "developer-tools",
    "documentation": "developer-tools",
    "linters": "developer-tools",
    "template-linters": "developer-tools",
    "test_clients": "developer-tools",
    "testing": "developer-tools",
    "buildout": "deployment",
    "deployment": "deployment",
    "webserver": "deployment",
}


def proposals(from_slugs, only_to=None):
    """Work out where each package should go, and what to leave alone.

    Returns the unambiguous moves and, separately, the packages whose grids
    disagree with each other. A package on both a cookiecutter grid and a
    linter grid is a judgement call, so it is reported and never moved.
    """
    grid_map = GRID_CATEGORY_MAP
    if only_to:
        grid_map = {g: c for g, c in grid_map.items() if c == only_to}

    rows = (
        GridPackage.objects.filter(grid__slug__in=grid_map)
        .filter(package__category__slug__in=from_slugs)
        .select_related("package", "package__category", "grid")
    )

    destinations = defaultdict(set)
    evidence = defaultdict(set)
    packages = {}

    for row in rows:
        destination = grid_map[row.grid.slug]
        # A package already in the right place is not a move.
        if destination == row.package.category.slug:
            continue
        packages[row.package_id] = row.package
        destinations[row.package_id].add(destination)
        evidence[row.package_id].add(row.grid.title)

    moves, conflicts = [], []
    for package_id, wanted in destinations.items():
        package = packages[package_id]
        grids = sorted(evidence[package_id])
        if len(wanted) == 1:
            moves.append((package, wanted.pop(), grids))
        else:
            conflicts.append((package, sorted(wanted), grids))

    moves.sort(key=lambda item: (item[1], item[0].slug))
    conflicts.sort(key=lambda item: item[0].slug)
    return moves, conflicts


@click.command()
@click.option(
    "--from",
    "from_slugs",
    default="other",
    help="Comma-separated categories to move packages out of. Default 'other'.",
)
@click.option(
    "--to",
    "only_to",
    default=None,
    help="Only propose moves into this category. Default is all of them.",
)
@click.option("--limit", default=0, type=int, help="Stop after this many. 0 means all.")
@click.option("--apply", "apply_moves", is_flag=True, help="Offer each move. Writes.")
@click.option(
    "--yes",
    "assume_yes",
    is_flag=True,
    help="Answer yes to every prompt. Only means anything with --apply.",
)
def command(from_slugs, only_to, limit, apply_moves, assume_yes):
    """
    Refile packages into the category their grids already imply.

    evaluate_packages asks Jev which of the installation types a package
    looks like, one API call at a time. For the packages that sit on a
    curated grid, that question has already been answered by a person, so
    this reads the answer off the grid instead of paying to ask for it.

    Read-only by default. --apply walks the moves one at a time, showing the
    grids behind each one, and writes only what is approved. Each prompt takes
    y, n or q to stop, and --yes answers them all.

    A package whose grids point at two different categories is reported and
    never moved: that is a judgement call, not a backfill.
    """
    if assume_yes and not apply_moves:
        console.print("[yellow]--yes does nothing without --apply.[/yellow]")

    from_slugs = [slug.strip() for slug in from_slugs.split(",") if slug.strip()]

    known = set(Category.objects.values_list("slug", flat=True))
    missing = sorted(set(from_slugs) - known)
    if missing:
        console.print(f"[red]No category {', '.join(missing)!r}.[/red]")
        raise SystemExit(1)

    wanted = set(GRID_CATEGORY_MAP.values())
    if only_to:
        if only_to not in wanted:
            console.print(
                f"[red]Nothing maps to {only_to!r}. "
                f"The map targets: {', '.join(sorted(wanted))}.[/red]"
            )
            raise SystemExit(1)
        wanted = {only_to}

    absent = sorted(wanted - known)
    if absent:
        console.print(
            f"[red]Category {', '.join(absent)!r} does not exist yet. "
            f"Run migrations first.[/red]"
        )
        raise SystemExit(1)

    moves, conflicts = proposals(from_slugs, only_to)
    if limit:
        moves = moves[:limit]

    if not moves and not conflicts:
        console.print("[yellow]Nothing to refile.[/yellow]")
        return

    if moves:
        table = Table(title="Packages their grids disagree with")
        table.add_column("Package")
        table.add_column("Filed as")
        table.add_column("Grids say")
        table.add_column("Because it is on")

        for package, destination, grids in moves:
            table.add_row(
                package.slug,
                f"[dim]{package.category.slug}[/dim]",
                f"[bold yellow]{destination}[/bold yellow]",
                truncate(", ".join(grids), 60),
            )

        console.print()
        console.print(table)

        by_destination = defaultdict(int)
        for _, destination, _ in moves:
            by_destination[destination] += 1
        summary = " | ".join(
            f"{destination}: {count}"
            for destination, count in sorted(by_destination.items())
        )
        console.print(f"\n{len(moves)} move(s) | {summary}")

    if conflicts:
        console.print(
            f"\n[bold]{len(conflicts)} package(s) left alone, "
            f"their grids disagree:[/bold]"
        )
        for package, wanted_slugs, grids in conflicts:
            console.print(
                f"  {package.slug}: {' or '.join(wanted_slugs)} "
                f"[dim](on {', '.join(grids)})[/dim]"
            )

    if not moves:
        return

    if not apply_moves:
        console.print("\n[dim]Read-only. Pass --apply to write any of this.[/dim]")
        return

    apply_category_moves(moves, assume_yes)


def apply_category_moves(moves, assume_yes):
    """Refile the approved packages. Nothing moves without a yes."""
    console.print("\n[bold]Refiling packages[/bold]")

    def describe(finding):
        package, destination, grids = finding
        return [
            f"\n  [bold]{package.slug}[/bold]: "
            f"{package.category.slug} -> [bold yellow]{destination}[/bold yellow]",
            f"  on {', '.join(grids)}",
            f"  {truncate(package.repo_description, 160) or '(no description)'}",
        ]

    destinations = {}
    moved = []

    for package, destination, _ in approve_each(console, moves, assume_yes, describe):
        if destination not in destinations:
            destinations[destination] = Category.objects.get(slug=destination)
        package.category = destinations[destination]
        moved.append(package)

    if moved:
        Package.objects.bulk_update(moved, ["category"])

    console.print(f"\n[bold]{len(moved)} package(s) refiled.[/bold]")
