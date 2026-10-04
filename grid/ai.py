"""Shared pieces for the Jev-backed grid review commands.

Jev is a decision model: it answers typed questions with a probability instead
of writing prose. That rules out `str` fields, so verdicts here are rubrics
(`IntEnum` with described levels), booleans carrying `BoolCriteria`, and
pick-one `Literal`s. Confidence comes back separately on the response.
"""

from __future__ import annotations

from enum import IntEnum
from typing import Annotated, Literal

import click
from django.conf import settings

from pydantic import BaseModel, Field
from pydantic_ai import Agent, BoolCriteria

MODEL = "typesafe:jev-latest"

# Project bar for acting on a model's answer. Below this a verdict is reported
# as unsure rather than counted for or against.
MIN_CONFIDENCE = 0.85

# Jev caps a request at 32k tokens of state and 64k overall, so the text built
# from a grid is trimmed well short of that.
MAX_PACKAGES_IN_PROMPT = 40
MAX_DESCRIPTION_CHARS = 300

INSTALLATION_TYPES = Literal[
    "apps",
    "frameworks",
    "other",
    "projects",
    "starter-projects",
]


class Quality(IntEnum):
    """Ordered rubric levels, lowest first."""

    UNUSABLE = 0
    """Fails at this entirely: absent, placeholder, or actively misleading."""

    WEAK = 1
    """Present but poor: vague, too broad, or missing most of what is needed."""

    DECENT = 2
    """Serviceable: a reader gets what they need, with rough edges."""

    STRONG = 3
    """Clearly good: specific, focused, and complete."""


GRID_CRITERIA = ("topic_coherence", "title_and_description", "useful_as_comparison")

# Asked alongside the rubrics, and reported on its own: a grid can score
# badly and still be worth fixing rather than deleting. Removal needs this
# answered no, or the grid to be empty, which the command checks itself.
GRID_REMOVAL = "topic_is_worth_a_grid"


class GridVerdict(BaseModel):
    """How good a comparison grid is.

    Deliberately three rubrics and no overall "is it good" boolean. That
    question was tried and Jev answered it at 0.12 and 0.78 confidence on
    grids it scored 3/3 and 0/3 on, because it restates the rubrics without
    saying what to measure. The quality call is computed from whichever
    rubrics clear the confidence bar instead.

    `topic_is_worth_a_grid` asks the one removal question Jev can see an
    answer to: whether a field of competing packages exists for the topic.
    Asking "should this be deleted" outright was tried and came back at 0.10
    to 0.80 across every grid, never clearing the bar, because it bundles
    emptiness, duplication, and topic into one boolean. Emptiness is a count
    the command already has, duplication needs the other grids, and only the
    topic question is left for the model.
    """

    topic_coherence: Quality = Field(
        description=(
            "Whether the packages listed belong to one focused topic rather "
            "than a loose grab-bag of loosely related things."
        )
    )
    title_and_description: Quality = Field(
        description=(
            "Whether the title names a specific topic and the description "
            "explains what belongs in the grid. A title like 'Grid' or a "
            "description like 'Description' is unusable."
        )
    )
    useful_as_comparison: Quality = Field(
        description=(
            "Whether there are enough packages, and enough comparable "
            "features, for this to work as a side-by-side comparison."
        )
    )
    topic_is_worth_a_grid: Annotated[
        bool,
        BoolCriteria(
            true=(
                "Several Django packages compete to solve the topic named in "
                "the title, so a developer could arrive wanting to pick one."
            ),
            false=(
                "The title names something with no field of competing Django "
                "packages behind it: a single package, a one-off, or a topic "
                "nobody shops around for."
            ),
        ),
    ]


class PackageVerdict(BaseModel):
    """Whether a package belongs in the grid it is listed on."""

    belongs_in_grid: Annotated[
        bool,
        BoolCriteria(
            true="The package is squarely the kind of thing the grid compares.",
            false="The package is off-topic for this grid and should be removed.",
        ),
    ]
    installation_type: INSTALLATION_TYPES = Field(
        description=(
            "How the package is installed and used. "
            "apps: a small component added to INSTALLED_APPS. "
            "frameworks: a large effort combining many modules or apps. "
            "projects: an individual deployed site or product. "
            "starter-projects: a pre-built project template or scaffold. "
            "other: anything not installed as an app, framework, or project, "
            "such as a standalone tool or library."
        )
    )


def truncate(text: str | None, limit: int = MAX_DESCRIPTION_CHARS) -> str:
    cleaned = " ".join((text or "").split())
    if len(cleaned) <= limit:
        return cleaned
    return cleaned[: limit - 1].rstrip() + "…"


def describe_grid(grid, packages, features) -> str:
    """Build the text Jev answers questions about."""
    lines = [
        f"Comparison grid: {grid.title}",
        f"Stated purpose: {truncate(grid.description) or '(no description)'}",
        f"Packages listed: {len(packages)}",
        f"Features compared: {', '.join(features) if features else '(none)'}",
        "",
        "Packages in this grid:",
    ]

    for package in packages[:MAX_PACKAGES_IN_PROMPT]:
        summary = truncate(package.repo_description, 160) or "(no description)"
        lines.append(f"- {package.title} [{package.category.title}]: {summary}")

    remaining = len(packages) - MAX_PACKAGES_IN_PROMPT
    if remaining > 0:
        lines.append(f"- ...and {remaining} more")

    return "\n".join(lines)


def describe_package_in_grid(grid, package) -> str:
    return "\n".join(
        [
            f"Comparison grid: {grid.title}",
            f"Grid purpose: {truncate(grid.description) or '(no description)'}",
            "",
            f"Candidate package: {package.title}",
            f"Currently filed under: {package.category.title}",
            f"Description: {truncate(package.repo_description) or '(none)'}",
            f"Repository: {package.repo_url or '(none)'}",
        ]
    )


def build_agent(output_type):
    """The key is read from the environment by the provider. Checking the
    setting here only buys a readable message instead of a provider error.
    """
    if not settings.TYPESAFE_API_KEY:
        raise click.ClickException(
            "TYPESAFE_API_KEY is not set, so there is nothing to ask. "
            "Add it to .env.local. See docs/docs/management_commands.md."
        )

    return Agent(MODEL, output_type=output_type)


def confidence_of(result) -> dict[str, float]:
    details = result.response.provider_details or {}
    return details.get("confidence") or {}


def is_confident(confidence: dict[str, float], field: str, threshold: float) -> bool:
    """Whether an answer clears the bar. Missing confidence counts as unsure."""
    value = confidence.get(field)
    return value is not None and value >= threshold


def format_answer(
    answer: str, confidence: dict[str, float], field: str, threshold: float
) -> str:
    value = confidence.get(field)
    if value is None:
        return f"{answer} (?)"
    if value < threshold:
        return f"[dim]{answer} ({value:.2f}, unsure)[/dim]"
    return f"{answer} ({value:.2f})"


SUPPORT_LEVELS = Literal[
    "supported",
    "partial",
    "not_supported",
    "unknown",
    "not_applicable",
]

# Cell text that the grid templates already render as an icon. These are
# answered locally so an obvious "yes" does not cost an API call.
LEGEND_YES = {"check", "yes", "good", "y", "true", "+", "++", "+++"}
LEGEND_NO = {"bad", "negative", "evil", "sucks", "no", "n", "false", "-", "--", "---"}

# Shown to Jev so it scores against real cells rather than an abstract idea of
# what a grid cell looks like. Picked from the shapes that actually turn up:
# a legend token, a version gate, a hedge, a pointer, and a non-answer.
ELEMENT_EXAMPLES = [
    ("yes", "supported"),
    ("Yes, since 2.0", "supported"),
    ("Only for Postgres", "partial"),
    ("Partial: read-only", "partial"),
    ("no", "not_supported"),
    ("Dropped in 4.0", "not_supported"),
    ("?", "unknown"),
    ("TODO", "unknown"),
    ("n/a for this package", "not_applicable"),
]


class ElementVerdict(BaseModel):
    """What one grid cell actually says about one package.

    The cells are free text with no convention beyond a loose icon legend, so
    this reads them back as one of five levels. `is_placeholder` is separate
    because "?" and "TODO" are unknown *and* worth deleting, while a genuine
    "nobody has checked" unknown is not.
    """

    support: SUPPORT_LEVELS = Field(
        description=(
            "What the cell says about whether this package has this feature. "
            "supported: it has it. "
            "partial: it has it with a caveat, a condition, or only in part. "
            "not_supported: it does not have it, or dropped it. "
            "unknown: the cell does not answer the question either way. "
            "not_applicable: the feature does not make sense for this package."
        )
    )
    is_placeholder: Annotated[
        bool,
        BoolCriteria(
            true=(
                "The text is filler rather than an answer: empty, '?', 'TODO', "
                "a repeat of the feature title, or otherwise says nothing."
            ),
            false="The text makes a claim a reader could act on.",
        ),
    ]


def legend_support(text: str | None) -> str | None:
    """Map the documented icon tokens without asking Jev. None means ask."""
    token = " ".join((text or "").split()).strip().lower().rstrip(".")
    if not token:
        return "unknown"
    if token in LEGEND_YES:
        return "supported"
    if token in LEGEND_NO:
        return "not_supported"
    return None


def describe_element(grid, package, feature, text: str) -> str:
    examples = "\n".join(
        f"- {sample!r} -> {label}" for sample, label in ELEMENT_EXAMPLES
    )
    return "\n".join(
        [
            "A cell from a Django package comparison grid. It records whether "
            "one package has one feature.",
            "",
            f"Comparison grid: {grid.title}",
            f"Package: {package.title}",
            f"Feature: {feature.title}",
            f"Feature description: {truncate(feature.description) or '(none)'}",
            "",
            f"Cell text: {truncate(text) or '(empty)'}",
            "",
            "How cells of this kind have been read before:",
            examples,
        ]
    )


class PackageOnlyVerdict(BaseModel):
    """What a package looks like when there is no grid to judge it against.

    `belongs_in_grid` has no meaning off a grid, and it was never earning its
    keep anyway: across real runs it came back between 0.04 and 0.84 and never
    cleared the bar. `description_is_usable` takes its place, because an
    untriaged package is usually untriaged for want of a description, and that
    is a different fix from a judgement call.
    """

    installation_type: INSTALLATION_TYPES = Field(
        description=(
            "How the package is installed and used. "
            "apps: a small component added to INSTALLED_APPS. "
            "frameworks: a large effort combining many modules or apps. "
            "projects: an individual deployed site or product. "
            "starter-projects: a pre-built project template or scaffold. "
            "other: anything not installed as an app, framework, or project, "
            "such as a standalone tool or library."
        )
    )
    description_is_usable: Annotated[
        bool,
        BoolCriteria(
            true=(
                "The description says what the package does, in enough detail "
                "to tell how it is installed and used."
            ),
            false=(
                "The description is missing, a placeholder, only the package "
                "name restated, or so vague that how it is used cannot be "
                "told from it."
            ),
        ),
    ]


def describe_package(package) -> str:
    """Build the text for a package with no grid behind it."""
    return "\n".join(
        [
            "A Python package listed on Django Packages, a directory of "
            "Django packages. It is on no comparison grid.",
            "",
            f"Package: {package.title}",
            f"Currently filed under: {package.category.title}",
            f"Description: {truncate(package.repo_description) or '(none)'}",
            f"Repository: {package.repo_url or '(none)'}",
            f"PyPI: {package.pypi_url or '(none)'}",
        ]
    )


def approve_each(console, items, assume_yes, describe):
    """Walk findings one at a time, yielding the ones approved for writing.

    Nothing is written without a yes. `describe` returns the lines shown
    before each prompt, so the reader can judge the recommendation on the
    package's own description rather than on the label alone. Answering q
    stops the walk and leaves the rest untouched.
    """
    for item in items:
        for line in describe(item):
            console.print(line)

        if assume_yes:
            console.print("  [dim]applying (--yes)[/dim]")
            yield item
            continue

        answer = click.prompt(
            "  apply? [y]es / [n]o / [q]uit",
            default="n",
            show_default=False,
            type=click.Choice(["y", "n", "q"], case_sensitive=False),
        ).lower()

        if answer == "q":
            console.print("  [dim]stopping, the rest are untouched[/dim]")
            return
        if answer == "y":
            yield item
