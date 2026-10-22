"""What Django removed, and when.

Empty on purpose. Every entry this table ever held was read out of
Django's documentation by a parser and then judged by hand, and a page
that tells package authors their code calls a dead API has no business
carrying a judgement call. Nothing is better than nearly right.

The fields are still there to be filled in: set `removed_in` on a
`ProbeSymbol` in the admin and that symbol appears on the page with
that version, and a rebuild will not touch it. `manage check_removals`
lists what Django's own docs name, ranked by how many packages call
it, so the list can be worked through deliberately rather than
generated.
"""

from __future__ import annotations

# Dotted path to the Django version that removed it. An entry covers
# everything under it, so `django.core.urlresolvers` would also answer
# for `django.core.urlresolvers.reverse`.
REMOVED_IN: dict[str, str] = {}


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
