"""The package score: six checks, 20 points each, faded by time since the last release.

`Package.score` is `score_package(package)["total_score"]`. The grids
sort on it and cut their comparison tables at `PACKAGE_SCORE_MIN`, the
search index weights packages by it, and the Package Score page lists
the checks with the points each one earned. One number, one place
(#1563).

The six point rules add up to 120, scaled to 100. That total is then
multiplied by `Package.activity_factor` (`ActivityRule`): 1.0 for a
year after the latest PyPI release, or the latest commit for a package
not on PyPI, then halving every eighteen months. Two and a half years
without a release leaves half the points, five years a sixth, ten
years nothing worth showing. A package drifts down its grids as it
ages instead of vanishing on a birthday, and comes back with the next
release.
"""

import math
from django.conf import settings
from pydantic import BaseModel

from package.models import Package


class CheckResult(BaseModel):
    score: int
    message: str
    # From `ActivityRule`: the whole score is multiplied by this.
    factor: float = 1.0


class ScoreRule(BaseModel):
    name: str
    description: str
    max_score: int
    documentation_url: str | None = None

    class Config:
        validate_assignment = True

    def check(self, package: Package) -> CheckResult:
        raise NotImplementedError("Subclasses should implement this!")


class ScoreRuleGroup(ScoreRule):
    rules: list[ScoreRule]

    def check(self, package: Package) -> CheckResult:
        results = [rule.check(package=package) for rule in self.rules]
        total_score = sum(result.score for result in results)
        max_possible_score = sum(rule.max_score for rule in self.rules)
        normalized_score = (
            (total_score / max_possible_score) * self.max_score
            if max_possible_score > 0
            else 0
        )
        messages = [result.message for result in results]
        return CheckResult(score=int(normalized_score), message=" ".join(messages))


class ActivityRule(ScoreRule):
    """Fade the score with time since the package last shipped.

    `Package.last_activity` is the latest PyPI release for a package on
    PyPI, since a project that commits but never ships is not maintained
    in any way its users can install, and the latest commit for one that
    is not on PyPI (no PyPI link, as for deployable apps and project
    templates). `Package.activity_factor` is 1.0 for the first
    `Package.ACTIVITY_FULL_YEARS` after that date, then halves every
    `Package.ACTIVITY_HALF_LIFE_YEARS`. The six point rules' total is
    multiplied by it, so an old package keeps its place relative to
    other old packages while falling below the grid cutoff. A package
    with no release or commit date on record scores 0. Computed from
    dates on every score run, never set by hand. Carries no points of
    its own.
    """

    name: str = "Activity Rule"
    description: str = (
        "The score keeps all its points for a year after the latest release "
        "(or latest commit, for a package not on PyPI), then halves every "
        "eighteen months"
    )
    max_score: int = 0
    documentation_url: str = f"{settings.DOCS_URL}/rules/#searchv3.rules.ActivityRule"

    def check(self, package: Package) -> CheckResult:
        last = package.last_activity
        if last is None:
            return CheckResult(
                score=0,
                message="No release or commit date on record, so the score is 0.",
                factor=0.0,
            )
        factor = package.activity_factor
        what = "release" if package.release_dates_it else "commit"
        if factor >= 1.0:
            return CheckResult(
                score=0,
                message=f"Last {what} {last:%B %Y}, within the last year: full score.",
                factor=1.0,
            )
        return CheckResult(
            score=0,
            message=(
                f"Last {what} {last:%B %Y}, {package.activity_age_text} ago: "
                f"score scaled to {package.activity_percent}%."
            ),
            factor=factor,
        )


class DeprecatedRule(ScoreRule):
    name: str = "Deprecated Rule"
    description: str = "Check if the package is deprecated"
    max_score: int = 20
    documentation_url: str = f"{settings.DOCS_URL}/rules/#searchv3.rules.DeprecatedRule"

    def check(self, package: Package) -> CheckResult:
        if package.is_deprecated:
            return CheckResult(score=0, message="Package is deprecated.")
        if package.date_repo_archived:
            return CheckResult(score=0, message="Package repository is archived.")
        return CheckResult(score=self.max_score, message="Package is not deprecated.")


class FavoritePackageRule(ScoreRule):
    name: str = "Favorite Package Rule"
    description: str = "Check if the package is favorite"
    max_score: int = 20
    documentation_url: str = (
        f"{settings.DOCS_URL}/rules/#searchv3.rules.FavoritePackageRule"
    )

    def check(self, package: Package) -> CheckResult:
        if package.has_favorite:
            return CheckResult(score=self.max_score, message="Package is favorite.")
        return CheckResult(score=0, message="Package is not favorite.")


class DescriptionRule(ScoreRule):
    name: str = "Description Rule"
    description: str = "Check if the package has a description"
    max_score: int = 20
    documentation_url: str = (
        f"{settings.DOCS_URL}/rules/#searchv3.rules.DescriptionRule"
    )

    def check(self, package: Package) -> CheckResult:
        if package.repo_description and package.repo_description.strip():
            return CheckResult(
                score=self.max_score, message="Package has a description."
            )
        return CheckResult(score=0, message="Package has no description.")


class DocumentationRule(ScoreRule):
    name: str = "Documentation Rule"
    description: str = "Check if the package has a documentation URL"
    max_score: int = 20
    documentation_url: str = (
        f"{settings.DOCS_URL}/rules/#searchv3.rules.DocumentationRule"
    )

    def check(self, package: Package) -> CheckResult:
        if package.documentation_url:
            return CheckResult(score=self.max_score, message="Documentation exists.")
        return CheckResult(score=0, message="No documentation.")


class DownloadsRule(ScoreRule):
    """Points for monthly PyPI downloads, on a log scale.

    Four points per tenfold above 10 downloads a month: 100 a month is 4,
    1,000 is 8, 10,000 is 12, 100,000 is 16, a million or more is 20.
    Linear per thousand, as before, gave nothing to seven in ten packages
    and the same 20 to everything from 20,000 up.
    """

    name: str = "Downloads Rule"
    description: str = (
        "Score based on monthly PyPI downloads, log scaled: 100 a month is 4 "
        "points, 1,000 is 8, 10,000 is 12, 100,000 is 16, a million is 20"
    )
    max_score: int = 20
    documentation_url: str = f"{settings.DOCS_URL}/rules/#searchv3.rules.DownloadsRule"

    # Points per tenfold, and the count that is worth nothing.
    points_per_decade: int = 4
    floor_downloads: int = 10

    def check(self, package: Package) -> CheckResult:
        if package.pypi_downloads:
            decades = math.log10(package.pypi_downloads / self.floor_downloads)
            score = int(min(max(decades, 0) * self.points_per_decade, self.max_score))
            return CheckResult(
                score=score,
                message=f"Package has {package.pypi_downloads:,} PyPI downloads a month.",
            )
        return CheckResult(score=0, message="No PyPI downloads data for the package.")


class ForkRule(ScoreRule):
    name: str = "Fork Rule"
    description: str = "Score based on the number of forks"
    max_score: int = 20
    documentation_url: str = f"{settings.DOCS_URL}/rules/#searchv3.rules.ForkRule"

    def check(self, package: Package) -> CheckResult:
        if package.repo_forks:
            score = min(package.repo_forks, self.max_score)
            return CheckResult(
                score=score,
                message=f"Package repository has {package.repo_forks} forks.",
            )
        return CheckResult(score=0, message="No forks data for the package repository.")


class UsageCountRule(ScoreRule):
    """Points for the people who clicked "I use this", on a log scale.

    Seven points per tenfold: one user is 1 (the floor: any usage at all
    is worth a point), 10 users are 7, 100 are 14, 1,000 or more are 20.
    Linear per user, as before, gave the full 20 to the 131 packages with
    20 or more users and could not tell 20 from 541.
    """

    name: str = "Usage Count Rule"
    description: str = (
        "Score based on how many people say they use the package, log scaled: "
        "1 user is 1 point, 10 are 7, 100 are 14, 1,000 or more are 20"
    )
    max_score: int = 20
    documentation_url: str = f"{settings.DOCS_URL}/rules/#searchv3.rules.UsageCountRule"

    points_per_decade: int = 7
    floor_points: int = 1

    def check(self, package: Package) -> CheckResult:
        # `score_package` querysets annotate `usage_count`; fall back to a
        # query for a bare instance.
        usage_count = getattr(package, "usage_count", None)
        if usage_count is None:
            usage_count = package.usage.count()
        if usage_count:
            points = math.log10(usage_count) * self.points_per_decade
            score = int(min(max(points, self.floor_points), self.max_score))
            return CheckResult(
                score=score,
                message=f"{usage_count:,} {'person says' if usage_count == 1 else 'people say'} they use the package.",
            )
        return CheckResult(score=0, message="Nobody has said they use the package yet.")


class WatchersRule(ScoreRule):
    name: str = "Watchers Rule"
    description: str = "Score based on the number of watchers"
    max_score: int = 20
    documentation_url: str = f"{settings.DOCS_URL}/rules/#searchv3.rules.WatchersRule"

    def check(self, package: Package) -> CheckResult:
        if package.repo_watchers:
            score = min(package.repo_watchers, self.max_score)
            return CheckResult(
                score=score,
                message=f"Package repository has {package.repo_watchers} watchers.",
            )
        return CheckResult(
            score=0, message="No watchers data for the package repository."
        )


def calc_package_weight(
    *, package: Package, rules: list[ScoreRule], max_score: int
) -> dict:
    total_score = 0
    breakdown = []
    messages = []
    factor = 1.0

    for rule in rules:
        result = rule.check(package=package)
        total_score += result.score
        factor *= result.factor
        messages.append(result.message)
        breakdown.append(
            {
                "rule": rule.name,
                "description": rule.description,
                "score": result.score,
                "max_score": rule.max_score,
                "message": result.message,
                "documentation_url": rule.documentation_url,
            }
        )

    max_possible_score = sum(rule.max_score for rule in rules)
    normalized_score = (
        (total_score / max_possible_score) * max_score if max_possible_score > 0 else 0
    )

    return {
        "total_score": int(normalized_score * factor),
        "message": " ".join(messages),
        "breakdown": breakdown,
        "factor": factor,
    }


# The checks that make up `Package.score`, in the order the score page
# lists them. The activity factor first, then six rules at 20 points
# each, 120 scaled to 100 and multiplied by the factor.
PACKAGE_RULES: list[ScoreRule] = [
    ActivityRule(),
    DeprecatedRule(),
    DescriptionRule(),
    DownloadsRule(),
    ForkRule(),
    UsageCountRule(),
    WatchersRule(),
]

PACKAGE_SCORE_MAX = 100


def score_package(package: Package) -> dict:
    """`Package.score` with its working: total_score, message, breakdown, factor.

    Reads `latest_version` and `usage`, so load the package with
    `select_related("latest_version")` and `annotate(usage_count=Count("usage",
    distinct=True))` when scoring in bulk.
    """
    return calc_package_weight(
        package=package, rules=PACKAGE_RULES, max_score=PACKAGE_SCORE_MAX
    )
