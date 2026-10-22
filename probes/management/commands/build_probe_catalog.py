from __future__ import annotations

import djclick as click
from django.db import transaction
from django.db.models import Q
from django.utils.timezone import now
from rich import print as rprint

from probes import stats as probe_stats
from probes.checkouts import ScanResult
from probes.models import ProbeSymbol

# Rows per INSERT ... ON CONFLICT. Large enough that tens of thousands
# of symbols take a handful of statements, small enough to keep each
# one well clear of any parameter limit.
BATCH_SIZE = 1000


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

    A row nothing uses any more has its counts set to zero, so an old
    number does not sit there looking current. --prune deletes those
    rows instead, unless someone has annotated them.
    """
    wanted = set(libraries)

    rows: list[tuple[str, str, str, int, int]] = []
    for row in probe_stats.symbol_rows():
        rows.append(
            (
                ProbeSymbol.Kind.SYMBOL,
                ScanResult.library_of(row.label),
                row.label,
                row.packages,
                row.uses,
            )
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

    in_scope = ProbeSymbol.objects.all()
    if wanted:
        in_scope = in_scope.filter(library__in=wanted)

    existing = set(in_scope.values_list("kind", "library", "name"))
    created = sum(1 for row in rows if row[:3] not in existing)
    updated = len(rows) - created

    timestamp = now()
    pruned = zeroed = 0

    if not dry_run:
        with transaction.atomic():
            # One upsert per batch instead of two queries per row. Only
            # the counts are in update_fields, which is what keeps the
            # curation columns out of reach of a rebuild.
            ProbeSymbol.objects.bulk_create(
                [
                    ProbeSymbol(
                        kind=kind,
                        library=library,
                        name=name,
                        packages=packages,
                        uses=uses,
                        counted_at=timestamp,
                    )
                    for kind, library, name, packages, uses in rows
                ],
                batch_size=BATCH_SIZE,
                update_conflicts=True,
                unique_fields=["kind", "library", "name"],
                update_fields=["packages", "uses", "counted_at", "modified"],
            )

            # Anything this rebuild did not touch is something no profile
            # uses any more. Read off the timestamp rather than a list of
            # the ids we wrote, which at this size is a very long query.
            stale = in_scope.filter(
                Q(counted_at__lt=timestamp) | Q(counted_at__isnull=True)
            )
            if prune:
                # Anything we have taken the trouble to annotate is kept
                # even when nothing uses it today, since that is the
                # record of why.
                pruned, _ = stale.filter(
                    deprecated=False, deprecated_in="", removed_in="", notes=""
                ).delete()
            zeroed = stale.update(packages=0, uses=0, counted_at=timestamp)

        probe_stats.invalidate()

    rprint(
        f"catalogue rows {len(rows):,}  created {created:,}  updated {updated:,}"
        + (f"  pruned {pruned:,}" if prune else "")
        + (f"  zeroed {zeroed:,}" if zeroed else "")
        + ("  [dim](dry run, nothing written)[/dim]" if dry_run else "")
    )

    if not dry_run:
        flagged = ProbeSymbol.objects.exclude(removed_in="").count()
        rprint(f"[dim]curated: {flagged:,} with a removal version[/dim]")
