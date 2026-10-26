"""Dry run of the package score against the stored `Package.score`.

Nothing is written. For every active package the command computes the
score from `searchv3.rules.PACKAGE_RULES`, sets it beside what is stored,
and answers the question that matters when tuning: what would each grid's
comparison table show if the computed score were the stored one, at the
current `PACKAGE_SCORE_MIN` or the `--new-min` given?

    manage.py compare_scores
    manage.py compare_scores --new-min 30
    manage.py compare_scores --grid ecommerce --grid rest
    manage.py compare_scores --csv scores.csv
"""

from __future__ import annotations

import csv
import statistics
from collections import defaultdict
from dataclasses import dataclass

import djclick as click
from django.conf import settings
from rich.console import Console
from rich.table import Table

from grid.models import Grid, GridPackage
from grid.scoring import cutoff_from_scores
from package.models import Package
from package.scores import scoring_queryset
from searchv3.rules import PACKAGE_RULES, score_package

BUCKETS = [("0", lambda s: s == 0)] + [
    (f"{lo}-{min(lo + 9, 100)}", lambda s, lo=lo: lo <= s <= min(lo + 9, 100))
    for lo in range(1, 101, 10)
]

# Column headings for the per-rule points, in PACKAGE_RULES order.
RULE_LABELS = [rule.name.removesuffix(" Rule").lower() for rule in PACKAGE_RULES]


@dataclass
class Row:
    pk: int
    slug: str
    title: str
    stored: int
    computed: int
    points: list[int]  # per rule, PACKAGE_RULES order
    factor: float  # the activity factor the total was multiplied by


@dataclass
class GridOutcome:
    """What one grid's comparison table shows under one set of scores."""

    shown: list[Row]
    cutoff: int

    @property
    def top(self) -> Row | None:
        return self.shown[0] if self.shown else None


def _load_rows() -> dict[int, Row]:
    rows = {}
    packages = scoring_queryset(Package.objects.active()).order_by("pk")
    for package in packages.iterator(chunk_size=1000):
        result = score_package(package)
        rows[package.pk] = Row(
            pk=package.pk,
            slug=package.slug,
            title=package.title,
            stored=package.score,
            computed=result["total_score"],
            points=[item["score"] for item in result["breakdown"]],
            factor=result["factor"],
        )
    return rows


def _load_grids(rows: dict[int, Row]) -> dict[Grid, list[Row]]:
    """Approved grids and their active packages, including grids with none."""
    members = defaultdict(list)
    pairs = GridPackage.objects.filter(grid__is_approved=True).values_list(
        "grid_id", "package_id"
    )
    for grid_id, package_id in pairs:
        if (row := rows.get(package_id)) is not None:
            members[grid_id].append(row)
    grids = Grid.objects.approved().only("pk", "slug", "title").order_by("title")
    return {grid: members.get(grid.pk, []) for grid in grids}


def _outcome(members: list[Row], score_of, score_min: int) -> GridOutcome:
    cutoff = cutoff_from_scores([score_of(row) for row in members], score_min)
    shown = sorted(
        (row for row in members if score_of(row) >= cutoff),
        key=lambda row: (-score_of(row), row.title.lower()),
    )
    return GridOutcome(shown=shown, cutoff=cutoff)


def _histogram(title: str, scores: list[int]) -> Table:
    table = Table(title=title, title_justify="left")
    table.add_column("score")
    table.add_column("packages", justify="right")
    table.add_column("share", justify="right")
    total = len(scores) or 1
    for label, member in BUCKETS:
        count = sum(1 for score in scores if member(score))
        table.add_row(label, f"{count:,}", f"{100 * count / total:.0f}%")
    return table


def _grid_detail(
    grid: Grid, members: list[Row], stored: GridOutcome, computed: GridOutcome
) -> Table:
    table = Table(
        title=(
            f"{grid.title} ({grid.slug}): {len(members)} active, "
            f"stored shows {len(stored.shown)} at >= {stored.cutoff}, "
            f"computed shows {len(computed.shown)} at >= {computed.cutoff}"
        ),
        title_justify="left",
    )
    table.add_column("package")
    for label in RULE_LABELS:
        table.add_column(label, justify="right")
    table.add_column("stored", justify="right")
    table.add_column("computed", justify="right")
    table.add_column("shown", justify="center")

    shown_stored = {row.pk for row in stored.shown}
    shown_computed = {row.pk for row in computed.shown}
    for row in sorted(members, key=lambda r: (-r.computed, -r.stored)):
        was, now = row.pk in shown_stored, row.pk in shown_computed
        marker = {
            (True, True): "both",
            (True, False): "[red]stored only[/red]",
            (False, True): "[green]computed only[/green]",
            (False, False): "[dim]neither[/dim]",
        }[(was, now)]
        table.add_row(
            row.title[:40],
            *(
                f"x{row.factor:.2f}" if rule.max_score == 0 else str(points)
                for rule, points in zip(PACKAGE_RULES, row.points)
            ),
            f"{row.stored:,}",
            str(row.computed),
            marker,
        )
    return table


def _write_csv(path: str, rows: dict[int, Row]) -> None:
    with open(path, "w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["pk", "slug", "stored", "computed", "factor", *RULE_LABELS])
        for row in rows.values():
            writer.writerow(
                [
                    row.pk,
                    row.slug,
                    row.stored,
                    row.computed,
                    f"{row.factor:.3f}",
                    *row.points,
                ]
            )


@click.command()
@click.option(
    "--new-min",
    type=int,
    default=None,
    help="Cutoff to apply to the computed score. Defaults to PACKAGE_SCORE_MIN.",
)
@click.option(
    "--grid",
    "grid_slugs",
    multiple=True,
    help="Print the package-level table for this grid slug. Repeatable.",
)
@click.option(
    "--changes",
    type=int,
    default=20,
    show_default=True,
    help="How many of the most-changed grids to list.",
)
@click.option(
    "--csv",
    "csv_path",
    type=click.Path(),
    default=None,
    help="Dump every package's scores and per-rule points to this CSV.",
)
def command(new_min, grid_slugs, changes, csv_path):
    """Compare the computed package score with the stored one, grid by grid. Writes nothing."""
    console = Console(width=max(Console().width, 180))
    stored_min = settings.PACKAGE_SCORE_MIN
    new_min = stored_min if new_min is None else new_min

    rows = _load_rows()
    grids = _load_grids(rows)

    console.print(
        f"[bold]{len(rows):,} active packages, {len(grids):,} approved grids[/bold]"
    )
    console.print(
        f"[dim]rules: {', '.join(RULE_LABELS)} (20 points each, scaled to 100)[/dim]"
    )
    console.print(f"[dim]stored cutoff {stored_min}, computed cutoff {new_min}[/dim]\n")

    # 1. Distributions.
    stored_scores = [row.stored for row in rows.values()]
    computed_scores = [row.computed for row in rows.values()]
    console.print(_histogram("Stored Package.score", stored_scores))
    console.print(_histogram("Computed score", computed_scores))
    console.print(
        f"median stored {statistics.median(stored_scores) if stored_scores else 0:g}, "
        f"median computed {statistics.median(computed_scores) if computed_scores else 0:g}, "
        f"{sum(1 for r in rows.values() if r.stored != r.computed):,} packages differ\n"
    )

    # Which rules carry the score.
    table = Table(title="Points by rule", title_justify="left")
    table.add_column("rule")
    table.add_column("packages scoring", justify="right")
    table.add_column("mean points", justify="right")
    for index, (label, rule) in enumerate(zip(RULE_LABELS, PACKAGE_RULES)):
        if rule.max_score == 0:
            factors = [row.factor for row in rows.values()]
            at_zero = sum(1 for f in factors if f < 0.005)
            table.add_row(
                label,
                f"[red]{at_zero:,} at zero[/red]",
                f"x{statistics.fmean(factors) if factors else 0:.2f} mean",
            )
            continue
        points = [row.points[index] for row in rows.values()]
        scoring = sum(1 for p in points if p > 0)
        table.add_row(
            label, f"{scoring:,}", f"{statistics.fmean(points) if points else 0:.1f}"
        )
    console.print(table)
    console.print()

    # 2. Grid-level effect, the #1758 table.
    stored_out = {}
    computed_out = {}
    for grid, members in grids.items():
        stored_out[grid] = _outcome(members, lambda r: r.stored, stored_min)
        computed_out[grid] = _outcome(members, lambda r: r.computed, new_min)

    def summarize(outcomes, score_min):
        with_packages = [g for g, m in grids.items() if m]
        return {
            "grid-package rows in comparison tables": sum(
                len(o.shown) for o in outcomes.values()
            ),
            "grids with packages but an empty table": sum(
                1 for g in with_packages if not outcomes[g].shown
            ),
            "grids showing 3 or more": sum(
                1 for o in outcomes.values() if len(o.shown) >= 3
            ),
            "grids showing everything (nothing clears the bar)": sum(
                1 for o in outcomes.values() if o.cutoff != score_min
            ),
        }

    stored_summary = summarize(stored_out, stored_min)
    computed_summary = summarize(computed_out, new_min)
    table = Table(title="Effect on the grids", title_justify="left")
    table.add_column("")
    table.add_column(f"stored >= {stored_min}", justify="right")
    table.add_column(f"computed >= {new_min}", justify="right")
    for key in stored_summary:
        table.add_row(key, f"{stored_summary[key]:,}", f"{computed_summary[key]:,}")
    top_changed = sum(
        1
        for g in grids
        if stored_out[g].top is not None
        and computed_out[g].top is not None
        and stored_out[g].top.pk != computed_out[g].top.pk
    )
    table.add_row("grids whose top package changes", "", f"{top_changed:,}")
    console.print(table)
    console.print()

    # 3. The grids that move most.
    churn = []
    for grid, members in grids.items():
        was = {r.pk for r in stored_out[grid].shown}
        now = {r.pk for r in computed_out[grid].shown}
        if was != now or (
            stored_out[grid].top
            and computed_out[grid].top
            and stored_out[grid].top.pk != computed_out[grid].top.pk
        ):
            churn.append((len(was ^ now), grid, len(was), len(now)))
    churn.sort(key=lambda item: (-item[0], item[1].title))
    if churn:
        table = Table(
            title=f"Most-changed grids ({len(churn):,} change at all, showing {min(changes, len(churn))})",
            title_justify="left",
        )
        table.add_column("grid")
        table.add_column("stored shows", justify="right")
        table.add_column("computed shows", justify="right")
        table.add_column("stored top")
        table.add_column("computed top")
        for _, grid, was, now in churn[:changes]:
            st, ct = stored_out[grid].top, computed_out[grid].top
            table.add_row(
                grid.slug,
                str(was),
                str(now),
                st.title[:30] if st else "-",
                (ct.title[:30] if ct else "-")
                if not (st and ct and st.pk == ct.pk)
                else "[dim]same[/dim]",
            )
        console.print(table)
        console.print()

    # 4. Requested grids in full.
    by_slug = {grid.slug: grid for grid in grids}
    for slug in grid_slugs:
        grid = by_slug.get(slug)
        if grid is None:
            console.print(f"[red]No approved grid with slug {slug!r}[/red]")
            continue
        console.print(
            _grid_detail(grid, grids[grid], stored_out[grid], computed_out[grid])
        )
        console.print()

    if csv_path:
        _write_csv(csv_path, rows)
        console.print(f"Wrote {len(rows):,} rows to {csv_path}")
