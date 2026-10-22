from __future__ import annotations

import json
import re

import djclick as click
from rich import print as rprint

from probes import django_docs
from probes import stats as probe_stats
from probes.models import ProbeSymbol
from probes.removals import TABLE

# Django removes things in feature releases, never in a patch. A
# three-part version here means the parser read a release number out
# of prose it did not understand, so the import stops rather than
# writing it.
VERSION = re.compile(r"^\d+\.\d+$")


@click.command()
@click.option(
    "--version",
    "versions",
    multiple=True,
    default=(
        "1.7",
        "1.8",
        "1.9",
        "1.10",
        "2.0",
        "2.1",
        "3.0",
        "3.1",
        "4.0",
        "4.1",
        "5.0",
        "5.1",
        "6.0",
    ),
    help="Release notes to read as well as the timeline",
)
@click.option("--dry-run", is_flag=True, help="Report without writing the table")
def command(versions: tuple[str, ...], dry_run: bool):
    """Rebuild probes/removals.json from Django's documentation.

    Prints what it kept and what it dropped, so the diff on the table
    can be read against a reason rather than taken on trust.
    """
    # A bullet's bare siblings are only taken when they match a name a
    # scan has seen, so the table grows from our own data rather than
    # from guesses about what a sentence meant.
    known = set(
        ProbeSymbol.objects.filter(kind=ProbeSymbol.Kind.SYMBOL).values_list(
            "name", flat=True
        )
    )
    documented = django_docs.documented(versions, known)

    for name, version in sorted(documented.items()):
        if not VERSION.match(version):
            raise click.ClickException(
                f"{version} is not a feature release, read for {name}"
            )

    table, unreleased = django_docs.released(documented)

    rprint(
        f"documented {len(documented):,}  kept {len(table):,}  "
        f"not released yet {unreleased:,}"
    )

    counts = dict(
        ProbeSymbol.objects.filter(
            kind=ProbeSymbol.Kind.SYMBOL, name__in=table
        ).values_list("name", "packages")
    )
    called = sum(1 for name in table if counts.get(name))
    rprint(f"[dim]{called:,} of them our packages call[/dim]")

    if dry_run:
        rprint("[dim](dry run, nothing written)[/dim]")
        return

    groups: dict[str, list[str]] = {}
    for name, version in table.items():
        groups.setdefault(version, []).append(name)

    data = {
        version: sorted(groups[version])
        for version in sorted(groups, key=django_docs.version_key)
    }
    TABLE.write_text(json.dumps(data, indent=2) + "\n")
    # The running process still holds the old table in memory; the next
    # one reads the new file. Drop the cached roll-ups so they are not
    # served from before the change for another fifteen minutes.
    probe_stats.invalidate()
    rprint(f"wrote {TABLE}")
