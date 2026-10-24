"""The replacement for `package.scores._calculate_score` (#1563).

A package scores 0 to 100. The number is how popular the package is,
scaled down by how recently it has been maintained:

    score = 100 * popularity * maintenance

Popularity blends GitHub stars and monthly PyPI downloads, each
log-scaled so that 50,000 stars is not worth a hundred times 500.
Maintenance is how fresh the latest PyPI release and the latest commit
are, with the release counting for more: a package that still ships is
maintained, one that only commits may not be (#1144). An abandoned
package decays toward zero no matter how many stars it has. Deprecated
and archived packages are a hard zero.

Signals that are missing are left out rather than read as zero. A
package with no PyPI release is judged on its commits alone, and one
with no download count on its stars alone. The exception is a package
with neither a release date nor a commit date: there is nothing to say
it is maintained, so it scores zero.

Everything tunable lives in `ScoreWeights`. `compare_scores` prints what
the grids would show under a given set, so tune there before changing
the defaults.

This module is not wired into `update_package_score` yet; `scores.py`
still runs the legacy formula until the comparison is signed off.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime

from django.utils import timezone

from package.models import Package

__all__ = ["ScoreInputs", "ScoreWeights", "calculate_score", "explain_score"]


@dataclass(frozen=True)
class ScoreWeights:
    """The knobs. Defaults are a starting point, not a verdict."""

    # Stars at or above this count as maximum popularity.
    stars_cap: int = 50_000
    # Monthly downloads at or above this count as maximum popularity.
    downloads_cap: int = 5_000_000
    # Share of popularity that downloads carry when they are known.
    # Stars carry the rest. Ignored when downloads are unknown.
    downloads_weight: float = 0.5
    # A release or commit this recent counts as fully fresh...
    fresh_days: int = 365
    # ...and one this old counts as not fresh at all. Linear in between.
    stale_days: int = 365 * 3
    # Share of maintenance that the release date carries when both a
    # release and a commit date are known. The commit carries the rest.
    release_weight: float = 0.6


DEFAULT_WEIGHTS = ScoreWeights()


@dataclass(frozen=True)
class ScoreInputs:
    """What the score is computed from, detached from the ORM."""

    repo_watchers: int = 0
    pypi_downloads: int = 0
    last_commit_date: datetime | None = None
    last_release_date: datetime | None = None
    is_deprecated: bool = False
    is_archived: bool = False

    @classmethod
    def from_package(cls, package: Package) -> ScoreInputs:
        """Needs `latest_version` loaded, or costs a query per package."""
        version = package.latest_version
        return cls(
            repo_watchers=package.repo_watchers or 0,
            pypi_downloads=package.pypi_downloads or 0,
            last_commit_date=package.last_commit_date,
            last_release_date=version.upload_time if version else None,
            is_deprecated=package.date_deprecated is not None,
            is_archived=package.date_repo_archived is not None,
        )


@dataclass(frozen=True)
class ScoreBreakdown:
    """`calculate_score` with its working shown, for the compare output."""

    score: int
    popularity: float
    maintenance: float
    stars_part: float | None
    downloads_part: float | None
    release_part: float | None
    commit_part: float | None
    zeroed_by: str | None = None


def _log_scaled(value: int, cap: int) -> float:
    """0 to 1, log-scaled, 1 at `cap` and above."""
    if value <= 0:
        return 0.0
    return min(1.0, math.log1p(value) / math.log1p(cap))


def _freshness(
    when: datetime | None, weights: ScoreWeights, now: datetime
) -> float | None:
    """1 while recent, falling linearly to 0 at `stale_days`. None if unknown."""
    if when is None:
        return None
    age_days = (now - when).total_seconds() / 86_400
    if age_days <= weights.fresh_days:
        return 1.0
    if age_days >= weights.stale_days:
        return 0.0
    span = weights.stale_days - weights.fresh_days
    return 1.0 - (age_days - weights.fresh_days) / span


def _blend(a: float | None, b: float | None, a_weight: float) -> float | None:
    """Weighted mean of what is known. None when neither is."""
    if a is None and b is None:
        return None
    if a is None:
        return b
    if b is None:
        return a
    return a_weight * a + (1 - a_weight) * b


def explain_score(
    inputs: ScoreInputs,
    weights: ScoreWeights = DEFAULT_WEIGHTS,
    *,
    now: datetime | None = None,
) -> ScoreBreakdown:
    now = now or timezone.now()

    if inputs.is_deprecated or inputs.is_archived:
        return ScoreBreakdown(
            score=0,
            popularity=0.0,
            maintenance=0.0,
            stars_part=None,
            downloads_part=None,
            release_part=None,
            commit_part=None,
            zeroed_by="deprecated" if inputs.is_deprecated else "archived",
        )

    stars_part = _log_scaled(inputs.repo_watchers, weights.stars_cap)
    # A zero download count is unknown as often as it is true: the column
    # defaults to 0 and is only filled for packages the stats job reached.
    downloads_part = (
        _log_scaled(inputs.pypi_downloads, weights.downloads_cap)
        if inputs.pypi_downloads > 0
        else None
    )
    popularity = _blend(downloads_part, stars_part, weights.downloads_weight) or 0.0

    release_part = _freshness(inputs.last_release_date, weights, now)
    commit_part = _freshness(inputs.last_commit_date, weights, now)
    maintenance = _blend(release_part, commit_part, weights.release_weight)
    zeroed_by = None
    if maintenance is None:
        maintenance = 0.0
        zeroed_by = "no release or commit date"

    return ScoreBreakdown(
        score=int(round(100 * popularity * maintenance)),
        popularity=popularity,
        maintenance=maintenance,
        stars_part=stars_part,
        downloads_part=downloads_part,
        release_part=release_part,
        commit_part=commit_part,
        zeroed_by=zeroed_by,
    )


def calculate_score(
    inputs: ScoreInputs,
    weights: ScoreWeights = DEFAULT_WEIGHTS,
    *,
    now: datetime | None = None,
) -> int:
    """0 to 100. See the module docstring for what goes in."""
    return explain_score(inputs, weights, now=now).score
