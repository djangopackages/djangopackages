"""What kind of answer a grid feature expects, and how to read a cell as one.

Every cell is stored as text and always will be: the API, the admin and
twenty years of hand-typed grids all read `Element.text`. A feature's
type does not change what is stored. It says how to read it, so a cell
can be validated when it is saved and, later, filtered, sorted or filled
by something that observed the package.

`parse` is the one function. Given a type and a cell's text it returns a
`Parsed` saying whether the text reads cleanly as that type, what value
it reads as, and any trailing note. The booleans use the same keyword
lists the comparison table has always used for its check and cross
icons, so a cell that renders as a check today parses as yes.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.db import models
from django.utils.translation import gettext_lazy as _

# The words the comparison table already turns into icons.
YES_KEYWORDS = ("check", "yes", "good", "+1", "+")
NO_KEYWORDS = ("bad", "negative", "evil", "sucks", "no", "-1", "-")
# Honest "we don't know" spellings. Empty is the commonest of them.
UNKNOWN_KEYWORDS = ("", "?", "n/a", "na", "unknown", "possible", "planned", "tbd")

# "1.8", "1.8+", "3.10", ">=4.2", "2.0-3.2", "1.11 LTS"
VERSION_TOKEN = re.compile(
    r"^(?:>=|<=|>|<|~=|==)?\d+(?:\.\d+)*\+?(?:-\d+(?:\.\d+)*)?$",
    re.IGNORECASE,
)
VERSION_SPLIT = re.compile(r"[,;/|]|\s+(?:and|or|to)\s+|\s+")
LTS = re.compile(r"\s*\blts\b", re.IGNORECASE)
# What follows a yes or no word when there is a note after it.
NOTE_BREAK = re.compile(r"^(?P<word>[^\s(,:;.-]+|\+|-)\s*(?P<note>.*)$", re.DOTALL)

_url = URLValidator(schemes=["http", "https"])


class FeatureType(models.TextChoices):
    TEXT = "text", _("Text")
    BOOLEAN = "boolean", _("Yes / no")
    VERSIONS = "versions", _("Version list")
    CHOICE = "choice", _("One of a list")
    URL = "url", _("URL")


# One line a grid editor sees when a cell does not fit its feature's type.
HINTS = {
    FeatureType.BOOLEAN: _(
        'Start with "yes" or "no", or leave it empty for unknown. Anything '
        'after the word is kept as a note, like "yes, via plugin".'
    ),
    FeatureType.VERSIONS: _(
        'Enter versions separated by commas, like "4.2, 5.1, 5.2" or "3.10+".'
    ),
    FeatureType.CHOICE: _("Pick one of this feature's choices."),
    FeatureType.URL: _("Enter one link starting with http:// or https://."),
}


@dataclass(frozen=True)
class Parsed:
    """How a cell's text reads as a feature's type.

    `ok` says the text is a clean instance of the type. `value` is the
    typed reading: True, False or None for a boolean, a list for
    versions, the canonical choice for a choice, the link for a url,
    the text itself for text. `note` is whatever trailed a boolean word.
    """

    ok: bool
    value: object = None
    note: str = ""
    choices: tuple[str, ...] = field(default=(), compare=False)


def _boolean(text: str) -> Parsed:
    low = text.strip().lower()
    if low in UNKNOWN_KEYWORDS:
        return Parsed(ok=True, value=None)
    if low in YES_KEYWORDS:
        return Parsed(ok=True, value=True)
    if low in NO_KEYWORDS:
        return Parsed(ok=True, value=False)
    match = NOTE_BREAK.match(text.strip())
    if match:
        word = match.group("word").lower()
        note = match.group("note").strip().lstrip(",:;-( ").rstrip(") ")
        if word in YES_KEYWORDS:
            return Parsed(ok=True, value=True, note=note)
        if word in NO_KEYWORDS:
            return Parsed(ok=True, value=False, note=note)
    return Parsed(ok=False, value=None)


def _versions(text: str) -> Parsed:
    # "1.11 LTS" means 1.11; the suffix is dropped before splitting.
    stripped = LTS.sub("", text).strip()
    if not stripped:
        return Parsed(ok=True, value=[])
    tokens = [t for t in VERSION_SPLIT.split(stripped) if t]
    for token in tokens:
        if not VERSION_TOKEN.match(token):
            return Parsed(ok=False, value=None)
    return Parsed(ok=True, value=tokens)


def _choice(text: str, choices: tuple[str, ...]) -> Parsed:
    stripped = text.strip()
    if not stripped:
        return Parsed(ok=True, value=None, choices=choices)
    for choice in choices:
        if stripped.casefold() == choice.casefold():
            return Parsed(ok=True, value=choice, choices=choices)
    return Parsed(ok=False, value=None, choices=choices)


def _link(text: str) -> Parsed:
    stripped = text.strip()
    if not stripped:
        return Parsed(ok=True, value=None)
    try:
        _url(stripped)
    except ValidationError:
        return Parsed(ok=False, value=None)
    return Parsed(ok=True, value=stripped)


def parse(feature_type: str, text: str, choices: tuple[str, ...] = ()) -> Parsed:
    """Read a cell's text as the given type.

    Text parses anything, since that is what every cell was until now.
    Empty text parses as every type, as "unknown", because a feature
    switched to a stricter type must not make its empty cells invalid.
    """
    text = text or ""
    if feature_type == FeatureType.BOOLEAN:
        return _boolean(text)
    if feature_type == FeatureType.VERSIONS:
        return _versions(text)
    if feature_type == FeatureType.CHOICE:
        return _choice(text, tuple(choices))
    if feature_type == FeatureType.URL:
        return _link(text)
    return Parsed(ok=True, value=text)


def hint(feature_type: str) -> str:
    return str(HINTS.get(feature_type, ""))
