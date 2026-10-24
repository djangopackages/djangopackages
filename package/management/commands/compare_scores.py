"""Dry run of the new package score (`package.scoring`) against the legacy one.

Nothing is written. For every active package the command computes the new
score and sets it beside the stored legacy `Package.score`, then answers
the question that matters for #1563: what would each grid's comparison
table show if the new score were the stored one?

    manage.py compare_scores
    manage.py compare_scores --new-min 30
    manage.py compare_scores --grid ecommerce --grid rest
    manage.py compare_scores --csv scores.csv
    manage.py compare_scores --stars-cap 20000 --release-weight 0.7
"""

from __future__ import annotations

import csv
import dataclasses
import statistics
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime

import djclick as click
from django.conf import settings
from django.utils import timezone
from rich.console import Console
from rich.table import Table

from grid.models import Grid, GridPackage
from grid.scoring import cutoff_from_scores
from package.models import Package
from package.scoring import (
    DEFAULT_WEIGHTS,
    ScoreBreakdown,
    ScoreInputs,
    ScoreWeights,
    explain_score,
)

LEGACY_BUCKETS = [
    ("<= 0", lambda s: s <= 0),
    ("1-9", lambda s: 1 <= s <= 9),
    ("10-49", lambda s: 10 <= s <= 49),
    ("50-99", lambda s: 50 <= s <= 99),
    ("100-499", lambda s: 100 <= s <= 499),
    ("500-999", lambda s: 500 <= s <= 999),
    ("1000+", lambda s: s >= 1000),
]
NEW_BUCKETS = [("0", lambda s: s == 0)] + [
    (f"{lo}-{min(lo + 9, 100)}", lambda s, lo=lo: lo <= s <= min(lo + 9, 100))
    for lo in range(1, 101, 10)
]


# Short forms of ScoreBreakdown.zeroed_by for the per-package table.
ZERO_NOTES = {
    "deprecated": "dep",
    "archived": "arch",
    "no release or commit date": "no dates",
}


@dataclass
class Row:
    pk: int
    slug: str
    title: str
    legacy: int
    inputs: ScoreInputs
    breakdown: ScoreBreakdown

    @property
    def new(self) -> int:
        return self.breakdown.score


@dataclass
class GridOutcome:
    """What one grid's comparison table shows under one set of scores."""

    shown: list[Row]
    cutoff: int

    @property
    def top(self) -> Row | None:
        return self.shown[0] if self.shown else None


def _load_rows(weights: ScoreWeights, now: datetime) -> dict[int, Row]:
    packages = (
        Package.objects.active()
        .select_related("latest_version")
        .only(
            "pk",
            "slug",
            "title",
            "score",
            "repo_watchers",
            "pypi_downloads",
            "last_commit_date",
            "date_deprecated",
            "date_repo_archived",
            "latest_version__upload_time",
        )
        .order_by("pk")
    )
    rows = {}
    for package in packages.iterator(chunk_size=1000):
        inputs = ScoreInputs.from_package(package)
        rows[package.pk] = Row(
            pk=package.pk,
            slug=package.slug,
            title=package.title,
            legacy=package.score,
            inputs=inputs,
            breakdown=explain_score(inputs, weights, now=now),
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


def _histogram(title: str, scores: list[int], buckets) -> Table:
    table = Table(title=title, title_justify="left")
    table.add_column("score")
    table.add_column("packages", justify="right")
    table.add_column("share", justify="right")
    total = len(scores) or 1
    for label, member in buckets:
        count = sum(1 for score in scores if member(score))
        table.add_row(label, f"{count:,}", f"{100 * count / total:.0f}%")
    return table


def _date(value: datetime | None) -> str:
    return value.date().isoformat() if value else "-"


def _grid_detail(
    grid: Grid, members: list[Row], legacy: GridOutcome, new: GridOutcome
) -> Table:
    table = Table(
        title=(
            f"{grid.title} ({grid.slug}): {len(members)} active, "
            f"legacy shows {len(legacy.shown)} at >= {legacy.cutoff}, "
            f"new shows {len(new.shown)} at >= {new.cutoff}"
        ),
        title_justify="left",
    )
    for name in ("package", "stars", "downloads", "released", "committed"):
        table.add_column(name, justify="right" if name != "package" else "left")
    table.add_column("legacy", justify="right")
    table.add_column("new", justify="right")
    table.add_column("shown", justify="center")

    shown_legacy = {row.pk for row in legacy.shown}
    shown_new = {row.pk for row in new.shown}
    for row in sorted(members, key=lambda r: (-r.new, -r.legacy)):
        was, now = row.pk in shown_legacy, row.pk in shown_new
        marker = {
            (True, True): "both",
            (True, False): "[red]legacy only[/red]",
            (False, True): "[green]new only[/green]",
            (False, False): "[dim]neither[/dim]",
        }[(was, now)]
        note = (
            f" [dim]({ZERO_NOTES[row.breakdown.zeroed_by]})[/dim]"
            if row.breakdown.zeroed_by
            else ""
        )
        table.add_row(
            row.title[:40],
            f"{row.inputs.repo_watchers:,}",
            f"{row.inputs.pypi_downloads:,}" if row.inputs.pypi_downloads else "-",
            _date(row.inputs.last_release_date),
            _date(row.inputs.last_commit_date),
            f"{row.legacy:,}",
            f"{row.new}{note}",
            marker,
        )
    return table


def _write_csv(path: str, rows: dict[int, Row]) -> None:
    with open(path, "w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "pk",
                "slug",
                "legacy",
                "new",
                "popularity",
                "maintenance",
                "stars",
                "downloads",
                "last_release",
                "last_commit",
                "zeroed_by",
            ]
        )
        for row in rows.values():
            b = row.breakdown
            writer.writerow(
                [
                    row.pk,
                    row.slug,
                    row.legacy,
                    row.new,
                    f"{b.popularity:.3f}",
                    f"{b.maintenance:.3f}",
                    row.inputs.repo_watchers,
                    row.inputs.pypi_downloads,
                    _date(row.inputs.last_release_date),
                    _date(row.inputs.last_commit_date),
                    b.zeroed_by or "",
                ]
            )


def _weight_options(func):
    """One --flag per ScoreWeights field, defaulting to the field's default."""
    for field in reversed(dataclasses.fields(ScoreWeights)):
        flag = "--" + field.name.replace("_", "-")
        func = click.option(
            flag,
            field.name,
            # Annotations are strings under `from __future__ import annotations`.
            type=int if field.type in (int, "int") else float,
            default=getattr(DEFAULT_WEIGHTS, field.name),
            show_default=True,
            help=f"ScoreWeights.{field.name}",
        )(func)
    return func


@click.command()
@click.option(
    "--new-min",
    type=int,
    default=None,
    help="Cutoff to apply to the new score. Defaults to PACKAGE_SCORE_MIN.",
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
    help="Dump every package's scores and inputs to this CSV.",
)
@_weight_options
def command(new_min, grid_slugs, changes, csv_path, **weight_kwargs):
    """Compare the new 0 to 100 package score with the stored legacy score. Writes nothing."""
    console = Console(width=max(Console().width, 140))
    weights = ScoreWeights(**weight_kwargs)
    legacy_min = settings.PACKAGE_SCORE_MIN
    new_min = legacy_min if new_min is None else new_min
    now = timezone.now()

    rows = _load_rows(weights, now)
    grids = _load_grids(rows)

    console.print(
        f"[bold]{len(rows):,} active packages, {len(grids):,} approved grids[/bold]"
    )
    console.print(f"[dim]weights: {weights}[/dim]")
    console.print(f"[dim]legacy cutoff {legacy_min}, new cutoff {new_min}[/dim]\n")

    # 1. Distributions.
    legacy_scores = [row.legacy for row in rows.values()]
    new_scores = [row.new for row in rows.values()]
    console.print(
        _histogram("Legacy score (stored Package.score)", legacy_scores, LEGACY_BUCKETS)
    )
    console.print(_histogram("New score", new_scores, NEW_BUCKETS))
    console.print(
        f"median legacy {statistics.median(legacy_scores) if legacy_scores else 0:g}, "
        f"median new {statistics.median(new_scores) if new_scores else 0:g}\n"
    )
    zeroed = defaultdict(int)
    for row in rows.values():
        if row.breakdown.zeroed_by:
            zeroed[row.breakdown.zeroed_by] += 1
    if zeroed:
        console.print(
            "new score is zero because: "
            + ", ".join(f"{k} ({v:,})" for k, v in zeroed.items())
            + "\n"
        )

    # 2. Grid-level effect, the #1758 table.
    legacy_out = {}
    new_out = {}
    for grid, members in grids.items():
        legacy_out[grid] = _outcome(members, lambda r: r.legacy, legacy_min)
        new_out[grid] = _outcome(members, lambda r: r.new, new_min)

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
            "grids on the above-zero fallback": sum(
                1 for o in outcomes.values() if o.cutoff != score_min
            ),
        }

    legacy_summary = summarize(legacy_out, legacy_min)
    new_summary = summarize(new_out, new_min)
    table = Table(title="Effect on the grids", title_justify="left")
    table.add_column("")
    table.add_column(f"legacy >= {legacy_min}", justify="right")
    table.add_column(f"new >= {new_min}", justify="right")
    for key in legacy_summary:
        table.add_row(key, f"{legacy_summary[key]:,}", f"{new_summary[key]:,}")
    top_changed = sum(
        1
        for g in grids
        if legacy_out[g].top is not None
        and new_out[g].top is not None
        and legacy_out[g].top.pk != new_out[g].top.pk
    )
    table.add_row("grids whose top package changes", "", f"{top_changed:,}")
    console.print(table)
    console.print()

    # 3. The grids that move most.
    churn = []
    for grid, members in grids.items():
        was = {r.pk for r in legacy_out[grid].shown}
        now_ = {r.pk for r in new_out[grid].shown}
        if was != now_ or (
            legacy_out[grid].top
            and new_out[grid].top
            and legacy_out[grid].top.pk != new_out[grid].top.pk
        ):
            churn.append((len(was ^ now_), grid, len(was), len(now_)))
    churn.sort(key=lambda item: (-item[0], item[1].title))
    if churn:
        table = Table(
            title=f"Most-changed grids ({len(churn):,} change at all, showing {min(changes, len(churn))})",
            title_justify="left",
        )
        table.add_column("grid")
        table.add_column("legacy shows", justify="right")
        table.add_column("new shows", justify="right")
        table.add_column("legacy top")
        table.add_column("new top")
        for _, grid, was, now_ in churn[:changes]:
            lt, nt = legacy_out[grid].top, new_out[grid].top
            table.add_row(
                grid.slug,
                str(was),
                str(now_),
                lt.title[:30] if lt else "-",
                (nt.title[:30] if nt else "-")
                if not (lt and nt and lt.pk == nt.pk)
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
        console.print(_grid_detail(grid, grids[grid], legacy_out[grid], new_out[grid]))
        console.print()

    if csv_path:
        _write_csv(csv_path, rows)
        console.print(f"Wrote {len(rows):,} rows to {csv_path}")
