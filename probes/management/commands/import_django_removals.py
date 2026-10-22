from __future__ import annotations

import importlib
import pathlib
import re

import django
import djclick as click
from rich import print as rprint

from probes import django_docs
from probes.models import ProbeSymbol

TABLE = pathlib.Path(__file__).resolve().parents[2] / "removals.py"

# Django removes things in feature releases, never in a patch. A
# three-part version here means the parser read a release number out
# of prose it did not understand, so the import stops rather than
# writing it.
VERSION = re.compile(r"^\d+\.\d+$")

HEADER = '''"""What Django removed, and when.

Written by `manage import_django_removals`, which reads Django's own
documentation: the deprecation timeline and the "removed" sections of
the release notes. A name is kept only when the docs name it in full
and the installed Django no longer has it, because those same bullets
also name the replacement to use, and a replacement is very much not
removed.

That second test cuts both ways and is meant to. A name that fails to
import for its own reasons, anything under `django.contrib.gis`
without GDAL for instance, is treated as present and left out. We lose
a few real removals that way. The alternative, which this page shipped
once, was calling four hundred live APIs dead.

Add anything missing by setting `removed_in` on a symbol in the admin,
which wins over this file and survives a rebuild.
"""

from __future__ import annotations

# Dotted path to the Django version that removed it. An entry covers
# everything under it, so `django.core.urlresolvers` also answers for
# `django.core.urlresolvers.reverse`.
REMOVED_IN: dict[str, str] = {
'''

FOOTER = '''}


def removed_in(symbol: str) -> str:
    """The Django version that removed this name, or "" if we do not know.

    An exact entry wins, then the longest module prefix, so one entry
    for a removed module answers for everything that was inside it.
    """
    if symbol in REMOVED_IN:
        return REMOVED_IN[symbol]

    best = ""
    for name in REMOVED_IN:
        if symbol.startswith(f"{name}.") and len(name) > len(best):
            best = name
    return REMOVED_IN[best] if best else ""
'''


def order(version: str) -> tuple[int, ...]:
    return tuple(int(part) for part in version.split("."))


def present(dotted: str) -> bool:
    """Whether the installed Django still has this name.

    A module answers for itself: `django.conf.urls` imports, so it is
    here, even though `django.conf` grows no `urls` attribute until
    something imports it. Only once that fails is the name read as an
    attribute of its parent.

    Anything we cannot answer counts as present, so an import that
    fails for its own reasons keeps a live name off the table rather
    than putting a dead one on it.
    """
    try:
        importlib.import_module(dotted)
        return True
    except ModuleNotFoundError as error:
        # Some other module is missing, which says nothing about this
        # name; only "there is no such module" sends us on.
        missing = error.name or ""
        if not (dotted == missing or dotted.startswith(f"{missing}.")):
            return True
    except Exception:
        return True

    module, _, attribute = dotted.rpartition(".")
    if not module:
        return True
    try:
        found = importlib.import_module(module)
    except Exception:
        return True
    try:
        return hasattr(found, attribute)
    except Exception:
        return True


@click.command()
@click.option(
    "--version",
    "versions",
    multiple=True,
    default=(
        "1.7", "1.8", "1.9", "1.10", "2.0", "2.1", "3.0", "3.1",
        "4.0", "4.1", "5.0", "5.1", "6.0",
    ),
    help="Release notes to read as well as the timeline",
)
@click.option("--dry-run", is_flag=True, help="Report without writing the table")
def command(versions: tuple[str, ...], dry_run: bool):
    """Rebuild probes/removals.py from Django's documentation.

    Prints what it kept and what it dropped, so the diff on the table
    can be read against a reason rather than taken on trust.
    """
    here = order(django.get_version())[:2]

    # A bullet's bare siblings are only taken when they match a name a
    # scan has seen, so the table grows from our own data rather than
    # from guesses about what a sentence meant.
    known = set(
        ProbeSymbol.objects.filter(kind=ProbeSymbol.Kind.SYMBOL).values_list(
            "name", flat=True
        )
    )
    documented = django_docs.documented(versions, known)
    table: dict[str, str] = {}
    unreleased = alive = 0

    for name, version in sorted(documented.items()):
        if not VERSION.match(version):
            raise click.ClickException(
                f"{version} is not a feature release, read for {name}"
            )
        if order(version) > here:
            unreleased += 1
            continue
        if present(name):
            alive += 1
            continue
        table[name] = version

    rprint(
        f"documented {len(documented):,}  kept {len(table):,}  "
        f"still here {alive:,}  not released yet {unreleased:,}"
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

    lines = []
    for version in sorted(groups, key=order):
        lines.append(f"    # Django {version}")
        lines += [f'    "{name}": "{version}",' for name in sorted(groups[version])]

    TABLE.write_text(HEADER + "\n".join(lines) + "\n" + FOOTER)
    rprint(f"wrote {TABLE}")
