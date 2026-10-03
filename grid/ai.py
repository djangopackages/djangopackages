"""Shared pieces for the Jev-backed grid review commands.

Jev is a decision model: it answers typed questions with a probability instead
of writing prose. That rules out `str` fields, so verdicts here are rubrics
(`IntEnum` with described levels), booleans carrying `BoolCriteria`, and
pick-one `Literal`s. Confidence comes back separately on the response.
"""

from __future__ import annotations

from enum import IntEnum
from typing import Annotated, Literal

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


class GridVerdict(BaseModel):
    """How good a comparison grid is.

    Deliberately three rubrics and no overall "is it good" boolean. That
    question was tried and Jev answered it at 0.12 and 0.78 confidence on
    grids it scored 3/3 and 0/3 on, because it restates the rubrics without
    saying what to measure. The recommendation is computed from whichever
    rubrics clear the confidence bar instead.
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
