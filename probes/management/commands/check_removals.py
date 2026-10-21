from __future__ import annotations

import re

import djclick as click
import httpx2
from rich import print as rprint

from probes.models import ProbeSymbol
from probes.removals import REMOVED_IN

DOCS = "https://raw.githubusercontent.com/django/django/main/docs"
TIMELINE = f"{DOCS}/internals/deprecation.txt"
RELEASE = f"{DOCS}/releases/{{version}}.txt"

TOKEN = re.compile(r"``([^`]+)``|:[a-z:]+:`~?([^`]+)`")
DOTTED = re.compile(r"[A-Za-z_][\w.]*")
SHORTHAND = (
    "conf.", "contrib.", "core.", "db.", "dispatch.", "forms.", "http.",
    "middleware.", "shortcuts.", "template.", "test.", "urls.", "utils.",
    "views.",
)


def names_in(bullet: str) -> list[str]:
    """The dotted Django paths a documentation bullet names.

    Only paths written out in full. Release notes often list siblings
    bare, as in "``ugettext()``, ``ugettext_lazy()``", and guessing the
    parent for those is how the old data went wrong.
    """
    found = []
    for token in TOKEN.finditer(bullet):
        name = (token.group(1) or token.group(2)).strip()
        name = name.split("<")[-1].rstrip(">").replace("()", "")
        if not DOTTED.fullmatch(name):
            continue
        if name.startswith("django."):
            found.append(name)
        elif name.startswith(SHORTHAND):
            found.append(f"django.{name}")
    return found


def from_timeline(text: str) -> dict[str, str]:
    """Removals Django has scheduled, by the version that does it.

    Sections headed with a year have not happened yet, so they are
    skipped; the page is about what is already gone.
    """
    found: dict[str, str] = {}
    parts = re.split(r"\n([0-9]+(?:\.[0-9]+)?)\n-{2,}\n", text)
    for i in range(1, len(parts), 2):
        version, body = parts[i], parts[i + 1]
        if "." not in version:
            continue
        for bullet in re.split(r"\n\n(?=\* )", body):
            for name in names_in(bullet):
                found.setdefault(name, version)
    return found


def from_release_notes(version: str, text: str) -> dict[str, str]:
    """Removals a release actually shipped, from its "removed" sections."""
    found: dict[str, str] = {}
    heading = re.compile(r"\n([^\n]*[Rr]emoved[^\n]*)\n([=~^-]{3,})\n")
    for match in heading.finditer(text):
        rest = text[match.end() :]
        underline = re.escape(match.group(2)[0])
        end = re.search(rf"\n[^\n]+\n{underline}{{3,}}\n", rest)
        body = rest[: end.start()] if end else rest
        for bullet in re.split(r"\n\n(?=\* )", body):
            for name in names_in(bullet):
                found.setdefault(name, version)
    return found


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
    short list to read rather than a guess. Nothing is written: the
    table is edited by hand, on purpose.
    """
    documented = from_timeline(httpx2.get(TIMELINE, timeout=30).text)
    for version in versions:
        response = httpx2.get(RELEASE.format(version=version), timeout=30)
        if response.status_code != 200:
            rprint(f"[yellow]no release notes for {version}[/yellow]")
            continue
        documented.update(from_release_notes(version, response.text))

    unknown = {
        name: version
        for name, version in documented.items()
        if name not in REMOVED_IN
    }
    counts = dict(
        ProbeSymbol.objects.filter(
            kind=ProbeSymbol.Kind.SYMBOL, name__in=unknown
        ).values_list("name", "packages")
    )

    rprint(
        f"documented {len(documented):,}  in our table {len(REMOVED_IN):,}  "
        f"not in our table {len(unknown):,}"
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
