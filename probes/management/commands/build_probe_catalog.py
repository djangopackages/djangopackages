from __future__ import annotations

import djclick as click
from django.utils.timezone import now
from rich import print as rprint

from probes import stats as probe_stats
from probes.models import ProbeSymbol


@click.command()
@click.option(
    "--library",
    "libraries",
    multiple=True,
    help="Only rebuild these libraries (default: all that were scanned)",
)
@click.option("--prune", is_flag=True, help="Delete rows nothing uses any more")
@click.option("--dry-run", is_flag=True, help="Report without writing")
def command(libraries: tuple[str, ...], prune: bool, dry_run: bool):
    """Roll the scanned symbols up into the catalogue.

    One row per library and name, with the counts replaced from the
    current profiles. The curation on each row, whether something is
    deprecated and which version removed it, is left alone: a rebuild
    that quietly dropped a deprecation would be worse than no catalogue.
    """
    wanted = set(libraries)

    rows: list[tuple[str, str, str, int, int]] = []
    for row in probe_stats.symbol_rows():
        library = row.label.partition(".")[0]
        rows.append(
            (ProbeSymbol.Kind.SYMBOL, library, row.label, row.packages, row.uses)
        )
    for row in probe_stats.setting_rows():
        rows.append(
            (ProbeSymbol.Kind.SETTING, "django", row.label, row.packages, row.uses)
        )
    for row in probe_stats.pattern_rows():
        # Patterns are named by whoever registered the probe, so the
        # library is the probe's namespace rather than an import.
        rows.append(
            (ProbeSymbol.Kind.PATTERN, "django", row.label, row.packages, row.uses)
        )

    if wanted:
        rows = [row for row in rows if row[1] in wanted]

    created = updated = 0
    timestamp = now()
    seen: list[int] = []

    for kind, library, name, packages, uses in rows:
        if dry_run:
            continue
        defaults = {"packages": packages, "uses": uses, "counted_at": timestamp}
        symbol, was_created = ProbeSymbol.objects.update_or_create(
            kind=kind, library=library, name=name, defaults=defaults
        )
        seen.append(symbol.pk)
        created += was_created
        updated += not was_created

    pruned = 0
    if prune and not dry_run:
        stale = ProbeSymbol.objects.exclude(pk__in=seen)
        if wanted:
            stale = stale.filter(library__in=wanted)
        # Anything we have taken the trouble to annotate is kept even
        # when nothing uses it today, since that is the record of why.
        stale = stale.filter(deprecated=False, removed_in="", notes="")
        pruned, _ = stale.delete()

    rprint(
        f"catalogue rows {len(rows):,}  created {created:,}  updated {updated:,}"
        + (f"  pruned {pruned:,}" if prune else "")
        + ("  [dim](dry run, nothing written)[/dim]" if dry_run else "")
    )

    if not dry_run:
        flagged = ProbeSymbol.objects.exclude(removed_in="").count()
        rprint(f"[dim]curated: {flagged:,} with a removal version[/dim]")
