"""What switching a feature to a stricter type would do to its cells.

Nothing is written. For every feature in scope the report says how many
of its filled cells read cleanly as a yes / no, a version list and a
URL, and which type looks like the fit. With --misses it also prints the
cells that would not parse under that type, so a grid owner can fix or
reword them before flipping the switch in the feature's edit form.
"""

from collections import Counter

import djclick as click
from rich.console import Console
from rich.table import Table

from grid.feature_types import FeatureType, parse
from grid.models import Element, Feature

console = Console()

CANDIDATES = (FeatureType.BOOLEAN, FeatureType.VERSIONS, FeatureType.URL)
# A type is suggested only when at least this share of filled cells
# parse as it, and only for features with enough cells to mean anything.
SUGGEST_SHARE = 0.9
SUGGEST_MIN_CELLS = 3


def suggest(counts: Counter, filled: int) -> str:
    if filled < SUGGEST_MIN_CELLS:
        return ""
    for candidate in CANDIDATES:
        if counts[candidate] / filled >= SUGGEST_SHARE:
            return candidate
    return ""


def report(features, show_misses: bool, proposed: str | None):
    table = Table(title="How each feature's cells read under each type")
    table.add_column("Grid")
    table.add_column("Feature")
    table.add_column("Type now")
    table.add_column("Filled", justify="right")
    for candidate in CANDIDATES:
        table.add_column(str(candidate.label), justify="right")
    table.add_column("Suggest")

    misses: list[tuple[Feature, str, list[str]]] = []
    for feature in features:
        texts = [
            text
            for text in Element.objects.filter(feature=feature).values_list(
                "text", flat=True
            )
            if text and text.strip()
        ]
        counts = Counter()
        for candidate in CANDIDATES:
            counts[candidate] = sum(1 for t in texts if parse(candidate, t).ok)
        suggestion = proposed or suggest(counts, len(texts))
        table.add_row(
            feature.grid.slug,
            feature.title,
            feature.type,
            str(len(texts)),
            *(f"{counts[c]}" for c in CANDIDATES),
            suggestion,
        )
        if show_misses and suggestion:
            bad = [t for t in texts if not parse(suggestion, t).ok]
            if bad:
                misses.append((feature, suggestion, bad))

    console.print(table)
    for feature, as_type, bad in misses:
        console.print(
            f"\n[bold]{feature.grid.slug} / {feature.title}[/bold] "
            f"as {as_type}: {len(bad)} cells would not parse"
        )
        for text in bad:
            console.print(f"  - {text[:100]!r}")


@click.command()
@click.option("--slug", default=None, help="Only one grid, by slug.")
@click.option("--feature", default=None, help="Only features matching this text.")
@click.option(
    "--type",
    "proposed",
    default=None,
    type=click.Choice([c.value for c in CANDIDATES]),
    help="Report misses under this type for every feature, instead of the suggested one.",
)
@click.option("--misses", is_flag=True, help="List the cells that would not parse.")
@click.option(
    "--min-filled",
    default=1,
    type=int,
    help="Skip features with fewer filled cells than this.",
)
def command(slug, feature, proposed, misses, min_filled):
    features = Feature.objects.select_related("grid").order_by("grid__slug", "title")
    if slug:
        features = features.filter(grid__slug=slug)
    if feature:
        features = features.filter(title__icontains=feature)

    features = [
        f
        for f in features
        if Element.objects.filter(feature=f).exclude(text="").count() >= min_filled
    ]
    if not features:
        console.print("No features with filled cells match.")
        return
    report(features, misses, proposed)
