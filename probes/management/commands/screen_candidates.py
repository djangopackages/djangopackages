"""Run the screening rules over the PyPI candidates.

    manage.py screen_candidates            # dry run: counts and examples
    manage.py screen_candidates --apply    # save reasons, hold the flagged rows

`pypi_discover` already does this after every run; this is for trying a
rule change against the whole table, or re-screening after enrichment
catches up. Rows a person has reviewed are never touched. See #1838.
"""

from __future__ import annotations

import djclick as click
from rich.console import Console
from rich.table import Table

from probes import screening


@click.command()
@click.option("--apply", is_flag=True, help="Save the reasons and statuses.")
@click.option(
    "--show",
    type=int,
    default=10,
    show_default=True,
    help="Example names to print per reason.",
)
def command(apply, show):
    """Flag candidates that look like spam, junk or a removed project."""
    console = Console()
    context = screening.Context.from_database()
    examples: dict[str, list[str]] = {code: [] for code in screening.REASONS}
    if show:
        for candidate in screening.screenable().iterator(chunk_size=500):
            for code in screening.screen(candidate, context):
                if len(examples[code]) < show:
                    examples[code].append(candidate.name)

    result = screening.screen_all(apply=apply, context=context)

    table = Table(title_justify="left")
    table.add_column("reason")
    table.add_column("weight")
    table.add_column("rows", justify="right")
    table.add_column("examples")
    for code, (label, weight) in screening.REASONS.items():
        table.add_row(
            label, weight, f"{result.by_reason[code]:,}", ", ".join(examples[code])
        )
    console.print(table)
    verb = "Saved" if apply else "Would save"
    console.print(
        f"Screened {result.seen:,} candidate(s): [bold]{result.held:,} held[/bold], "
        f"{result.released:,} released back to new. {verb} {result.changed:,} change(s)."
    )
    if not apply:
        console.print("Dry run. Pass --apply to save.")
