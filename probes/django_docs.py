"""Reading Django's own documentation for what it has removed.

Two documents say it: the deprecation timeline, which lists every
release and what it took out, and the "removed" sections of each
release's notes. Both are prose, so this reads the dotted paths out of
them and nothing else. What a bullet means about a name it mentions,
whether it was removed or merely changed or offered as the
replacement, is not something a parser can tell, which is why the
caller has to filter and why the table they feed is small.
"""

from __future__ import annotations

import re

import httpx2

DOCS = "https://raw.githubusercontent.com/django/django/main/docs"
TIMELINE = f"{DOCS}/internals/deprecation.txt"
RELEASE = f"{DOCS}/releases/{{version}}.txt"

SETTINGS = "django.conf.global_settings"
TOKEN = re.compile(r"``([^`]+)``|:[a-z:]+:`~?([^`]+)`")
DOTTED = re.compile(r"[A-Za-z_][\w.]*")
SHORTHAND = (
    "conf.",
    "contrib.",
    "core.",
    "db.",
    "dispatch.",
    "forms.",
    "http.",
    "middleware.",
    "shortcuts.",
    "template.",
    "test.",
    "urls.",
    "utils.",
    "views.",
)


def names_in(bullet: str, known: set[str] | None = None) -> list[str]:
    """The dotted Django paths a documentation bullet names.

    Paths written out in full, the shorthand the notes use when no
    full path is in the same bullet, and the siblings written bare,
    as in "``ugettext()``, ``ugettext_lazy()``, ``ungettext()``". A
    bare name is only taken when putting it under the first full
    path's parent produces something in `known`, the names our scans
    have actually seen, because the alternative is inventing dotted
    paths out of prose: "Message" in a sentence about contrib became
    `django.contrib.Message` the first time this was written.
    """
    found = []
    shorthand = []
    bare = []
    for token in TOKEN.finditer(bullet):
        name = (token.group(1) or token.group(2)).strip()
        name = name.split("<")[-1].rstrip(">").replace("()", "")
        if not DOTTED.fullmatch(name):
            continue
        if name.startswith("django."):
            found.append(name)
        elif name.startswith(SHORTHAND) and not name.endswith(".py"):
            shorthand.append(f"django.{name}")
        elif "." not in name:
            bare.append(name)

    # Shorthand is how the notes write a path when the bullet has no
    # room for the full one. A bullet that spells one out in full is
    # not using shorthand, so a `views.feed` next to it is prose about
    # a file, not a second path.
    if not found:
        found = shorthand

    if known:
        # A bare name in capitals is a setting. The notes write them
        # that way with no path at all, "the ``MIDDLEWARE_CLASSES``
        # setting will be removed", and settings live in one module.
        found += [
            f"{SETTINGS}.{name}"
            for name in bare
            if name.isupper() and f"{SETTINGS}.{name}" in known
        ]

    if found and known:
        parent = found[0].rpartition(".")[0]
        found += [
            f"{parent}.{name}"
            for name in bare
            if not name.isupper() and f"{parent}.{name}" in known
        ]
    return found


def from_timeline(text: str, known: set[str] | None = None) -> dict[str, str]:
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
            for name in names_in(bullet, known):
                found.setdefault(name, version)
    return found


def from_release_notes(
    version: str, text: str, known: set[str] | None = None
) -> dict[str, str]:
    """Removals a release actually shipped, from its "removed" sections."""
    found: dict[str, str] = {}
    heading = re.compile(r"\n([^\n]*[Rr]emoved[^\n]*)\n([=~^-]{3,})\n")
    for match in heading.finditer(text):
        rest = text[match.end() :]
        underline = re.escape(match.group(2)[0])
        end = re.search(rf"\n[^\n]+\n{underline}{{3,}}\n", rest)
        body = rest[: end.start()] if end else rest
        for bullet in re.split(r"\n\n(?=\* )", body):
            for name in names_in(bullet, known):
                found.setdefault(name, version)
    return found


def fetch(url: str) -> str:
    response = httpx2.get(url, timeout=30)
    response.raise_for_status()
    return response.text


def documented(
    versions: tuple[str, ...] = (), known: set[str] | None = None
) -> dict[str, str]:
    """Every dotted name the docs mention in a removal, with its version.

    The timeline covers every release at once. Release notes are read
    for the versions named, because their wording catches things the
    timeline words differently, `django.utils.six` among them.
    """
    seen: dict[str, list[str]] = {}
    for source in [from_timeline(fetch(TIMELINE), known)] + [
        from_release_notes(version, fetch(RELEASE.format(version=version)), known)
        for version in versions
    ]:
        for name, version in source.items():
            seen.setdefault(name, []).append(version)

    # The last release to mention a name is the one that removed it.
    # Earlier mentions are the deprecation, or an argument going, and
    # taking those would date a removal years before it happened.
    return {
        name: max(found, key=lambda v: tuple(int(part) for part in v.split(".")))
        for name, found in seen.items()
    }
