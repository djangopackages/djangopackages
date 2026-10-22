from __future__ import annotations

import djclick as click
from rich import print as rprint

from probes import django_docs
from probes.models import ProbeSymbol
from probes.removals import REMOVED_IN


@click.command()
@click.option(
    "--version",
    "versions",
    multiple=True,
    help="Release notes to read as well as the timeline, like 6.1",
)
def command(versions: tuple[str, ...]):
    """Compare our removals table against Django's documentation.

    Prints what the docs name that we do not have, and how much of it
    our packages actually use, so a new Django release turns into a
    short list to read rather than a guess. Nothing is written: run
    import_django_removals to rebuild the table.

    The docs are read the same way the import reads them, with the
    names our scans have seen and without removals that have not
    happened yet, so what this reports is what an import would add.
    """
    known = set(
        ProbeSymbol.objects.filter(kind=ProbeSymbol.Kind.SYMBOL).values_list(
            "name", flat=True
        )
    )
    documented, unreleased = django_docs.released(
        django_docs.documented(versions, known)
    )

    unknown = {
        name: version for name, version in documented.items() if name not in REMOVED_IN
    }
    counts = dict(
        ProbeSymbol.objects.filter(
            kind=ProbeSymbol.Kind.SYMBOL, name__in=unknown
        ).values_list("name", "packages")
    )

    rprint(
        f"documented {len(documented):,}  in our table {len(REMOVED_IN):,}  "
        f"not in our table {len(unknown):,}  not released yet {unreleased:,}"
    )
    if not unknown:
        return

    rprint("\n[bold]Worth reading, most used first:[/bold]")
    for name, version in sorted(
        unknown.items(), key=lambda item: (-counts.get(item[0], 0), item[0])
    ):
        packages = counts.get(name, 0)
        if packages:
            rprint(f"  {packages:>4} packages  [{version}]  {name}")
    unused = sum(1 for name in unknown if not counts.get(name))
    rprint(f"  [dim]and {unused:,} nobody calls[/dim]")
