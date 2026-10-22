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

# Django's docs say a thing is removed in one of a few set phrases, and
# everything after that phrase is advice about what to use instead.
# Reading only what comes before it is how the replacement in "force_text
# is removed, use force_str" stays off a list of dead APIs.
REMOVAL = re.compile(r"\b(?:will be|is|are|was|were|has been|have been)\s+removed\b")

# Words a bullet may put around the name without changing what it
# says: "The ``django.utils.six`` module will be removed" is about
# six. Anything else in the subject, "support for", "the safe
# parameter of", "old-style middleware using", means the sentence is
# about something other than the name itself, and the bullet is left
# alone. Terse to the point of losing real removals, which is the
# direction to lose them in.
FILLER = frozenset(
    """
    a an and the this these those
    also as at by for from in into of on or to with
    alias class classes decorator decorators field fields function
    functions method methods model models module modules package
    packages setting settings subclass subclasses tag tags template
    templates value values view views widget widgets
    deprecated legacy old private undocumented
    """.split()
)
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


def removal_subject(bullet: str, heading_says_removed: bool = False) -> str:
    """The part of a bullet that says what was removed, or "".

    Empty when the bullet does not assert a removal at all, or when
    it says anything beyond naming what went: the removal of one
    argument of a class, or of support for using it some way, leaves
    the class itself alive.
    """
    match = REMOVAL.search(bullet)
    if match:
        subject = bullet[: match.start()]
    elif heading_says_removed:
        # Under a heading that says these are removed, a bullet can
        # just name the thing and then talk about what to do instead:
        # "``django.utils.six`` - Remove usage of this vendored
        # library". The name is everything before that turn.
        subject = re.split(r"\s+[-\u2013]\s+|(?<=`)\.\s", bullet)[0]
    else:
        return ""

    # What is left once the names and the words that may surround them
    # are taken out. Anything at all means the sentence is doing more
    # than naming a thing that went.
    rest = TOKEN.sub(" ", subject).replace("*", " ")
    leftover = [
        word
        for word in re.findall(r"[A-Za-z_][\w.]*", rest)
        if word.lower() not in FILLER
    ]
    if leftover:
        return ""
    return subject


def names_in(
    bullet: str,
    known: set[str] | None = None,
    heading_says_removed: bool = False,
) -> list[str]:
    """The dotted Django paths a documentation bullet names.

    Only from a bullet that says something was removed, and only from
    the part of it that names what went.

    Paths written out in full, the shorthand the notes use when no
    full path is in the same bullet, and the siblings written bare,
    as in "``ugettext()``, ``ugettext_lazy()``, ``ungettext()``". A
    bare name is only taken when putting it under the first full
    path's parent produces something in `known`, the names our scans
    have actually seen, because the alternative is inventing dotted
    paths out of prose: "Message" in a sentence about contrib became
    `django.contrib.Message` the first time this was written.
    """
    bullet = removal_subject(bullet, heading_says_removed)
    if not bullet:
        return []

    found = []
    shorthand = []
    bare = []
    first_path = first_bare = None
    for token in TOKEN.finditer(bullet):
        name = (token.group(1) or token.group(2)).strip()
        name = name.split("<")[-1].rstrip(">").replace("()", "")
        if not DOTTED.fullmatch(name):
            continue
        if name.startswith("django."):
            if first_path is None:
                first_path = token.start()
            found.append(name)
        elif name.startswith(SHORTHAND) and not name.endswith(".py"):
            shorthand.append(f"django.{name}")
        elif "." not in name:
            if first_bare is None:
                first_bare = token.start()
            bare.append(name)

    # Shorthand is how the notes write a path when the bullet has no
    # room for the full one. A bullet that spells one out in full is
    # not using shorthand, so a `views.feed` next to it is prose about
    # a file, not a second path.
    if not found:
        found = shorthand

    known = known or set()

    # A bare name in capitals is a setting. The notes write them that
    # way with no path at all, "the ``MIDDLEWARE_CLASSES`` setting
    # will be removed", and settings live in one module.
    settings = [
        f"{SETTINGS}.{name}"
        for name in bare
        if name.isupper() and f"{SETTINGS}.{name}" in known
    ]
    bare = [name for name in bare if not name.isupper()]

    # Shorthand next to a full path means the full path is where the
    # shorthand lives, as in "``views.feed()`` in
    # ``django.contrib.syndication``". The container outlives what was
    # taken out of it, so a bullet shaped that way says nothing we can
    # use about the path it names.
    if shorthand and found:
        return settings
    if not found:
        found = shorthand
    if not found:
        return settings

    if bare:
        # Either the bare names live in the path, "``remove_tags()``
        # in ``django.utils.html``", or they are its siblings,
        # "``ugettext()``, ``ugettext_lazy()``". Our own scans decide
        # which reading produces real names, and if neither does the
        # bullet is left alone rather than read generously.
        inside = [f"{found[0]}.{name}" for name in bare]
        beside = [f"{found[0].rpartition('.')[0]}.{name}" for name in bare]
        # A list of siblings puts the full path first and the rest
        # bare. A bare name before the path is something that lived in
        # it or pointed at it, "The ``ChoicesMeta`` alias to
        # ``...ChoicesType``", and then the path stays.
        leads = first_bare is not None and first_bare < (first_path or 0)
        if any(name in known for name in inside):
            return settings + [name for name in inside if name in known]
        if any(name in known for name in beside):
            kept = [name for name in beside if name in known]
            return settings + kept if leads else settings + found + kept
        return settings

    return settings + found


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
            for name in names_in(bullet, known, heading_says_removed=True):
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
