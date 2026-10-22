"""What Django removed, and when.

The table lives in removals.json, grouped by the Django version that
removed each name. It is written by `manage import_django_removals`,
which reads Django's own documentation: the deprecation timeline and the
"removed" sections of the release notes. Keeping it as data means the
import never writes Python, so this lookup cannot drift from a copy of
itself inside the command.

Nothing here asks the installed Django anything. A name is kept when a
bullet says it was removed and names it before saying so; the advice
that follows, "use force_str() instead", is not read, and neither is a
bullet that only removes an argument or an attribute of something
still here. What the documentation does not say plainly, this does not
claim.

Add anything missing by setting `removed_in` on a symbol in the admin,
which wins over this file and survives a rebuild.
"""

from __future__ import annotations

import json
from pathlib import Path

TABLE = Path(__file__).resolve().with_name("removals.json")


def load(path: Path = TABLE) -> dict[str, str]:
    """The table as dotted path to version, flattened from its groups."""
    groups: dict[str, list[str]] = json.loads(path.read_text())
    return {name: version for version, names in groups.items() for name in names}


# Dotted path to the Django version that removed it. An entry covers
# everything under it, so `django.core.urlresolvers` also answers for
# `django.core.urlresolvers.reverse`.
REMOVED_IN: dict[str, str] = load()


def removed_in(symbol: str) -> str:
    """The Django version that removed this name, or "" if we do not know.

    An exact entry wins, then the longest module prefix, so one entry
    for a removed module answers for everything that was inside it.
    Walking the symbol's own prefixes, longest first, is a handful of
    dict lookups rather than a pass over the whole table.
    """
    parts = symbol.split(".")
    for end in range(len(parts), 0, -1):
        version = REMOVED_IN.get(".".join(parts[:end]))
        if version:
            return version
    return ""
