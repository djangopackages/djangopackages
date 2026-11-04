"""The package score: eight checks, 20 points each, faded by time since the last release.

`Package.score` is `score_package(package)["total_score"]`. The grids
sort on it and cut their comparison tables at `PACKAGE_SCORE_MIN`, the
search index weights packages by it, and the Package Score page lists
the checks with the points each one earned. One number, one place
(#1563).

The eight point rules add up to 160, scaled to 100.
A rule with nothing to read for a package (the version check, for one with no PyPI data) is left out of both totals.
That total is then multiplied by `Package.activity_factor` (`ActivityRule`): 1.0 for a
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
from package.utils import documentation_url_problem
from probes.version_support import support_grade, version_support


class CheckResult(BaseModel):
    score: int
    message: str
    # From `ActivityRule`: the whole score is multiplied by this.
    factor: float = 1.0
    # True when the rule has nothing to read for this package. Its points
    # leave the total too, so missing data is not scored as zero.
    skipped: bool = False


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
        # Integer arithmetic: 57 / 100 * 100 is 56.999 in floating point.
        normalized_score = (
            total_score * self.max_score // max_possible_score
            if max_possible_score > 0
            else 0
        )
        messages = [result.message for result in results]
        return CheckResult(score=normalized_score, message=" ".join(messages))


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
    """Points for a documentation site.

    The documentation URL has to lead somewhere the package page does
    not already: a link back to the repository, to a README, or to the
    PyPI page scores nothing (`package.utils.documentation_url_problem`
    is the test, the same one the forms apply). A wiki or a docs folder
    inside the repository counts.
    """

    name: str = "Documentation Rule"
    description: str = (
        "Check if the package links a documentation site, not just its "
        "repository, README or PyPI page"
    )
    max_score: int = 20
    documentation_url: str = (
        f"{settings.DOCS_URL}/rules/#searchv3.rules.DocumentationRule"
    )

    def check(self, package: Package) -> CheckResult:
        url = (package.documentation_url or "").strip()
        if not url:
            return CheckResult(score=0, message="No documentation URL.")
        if problem := documentation_url_problem(url, repo_url=package.repo_url):
            what = {
                "pypi": "the PyPI page",
                "repo": "the repository",
                "readme": "a README",
                "forge": "a repository page",
            }[problem]
            return CheckResult(
                score=0,
                message=f"The documentation URL is {what}, which does not count.",
            )
        return CheckResult(score=self.max_score, message=f"Documentation at {url}.")


def log_points(count: int, points_per_decade: int, max_score: int) -> int:
    """`points_per_decade` per tenfold of `count`, capped. One is zero points."""
    if count <= 0:
        return 0
    return int(min(math.log10(count) * points_per_decade, max_score))


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
    """Points for repository forks, on a log scale.

    Five points per tenfold: 10 forks are 5, 100 are 10, 1,000 are 15,
    10,000 or more are 20. Linear, as before, gave full marks to every
    repository with 20 forks, which was a quarter of the catalogue.
    """

    name: str = "Fork Rule"
    description: str = (
        "Score based on repository forks, log scaled: 10 forks are 5 points, "
        "100 are 10, 1,000 are 15, 10,000 are 20"
    )
    max_score: int = 20
    documentation_url: str = f"{settings.DOCS_URL}/rules/#searchv3.rules.ForkRule"

    points_per_decade: int = 5

    def check(self, package: Package) -> CheckResult:
        if package.repo_forks:
            score = log_points(
                package.repo_forks, self.points_per_decade, self.max_score
            )
            return CheckResult(
                score=score,
                message=f"Package repository has {package.repo_forks:,} forks.",
            )
        return CheckResult(score=0, message="No forks data for the package repository.")


class UsageCountRule(ScoreRule):
    """Points for the people behind the package: "I use this" clicks or
    favorites, whichever is higher, on a log scale.

    Seven points per tenfold of either count: 10 are 7, 100 are 14, 1,000
    or more are 20. Each count is scaled on its own and the higher wins,
    so a package with 13 favorites and 3 users scores as 13. The floor is
    one point for any package with a release or commit in the last
    `maintained_years`, whether or not anyone has clicked yet: a
    maintained package is in use somewhere. Only an unmaintained package
    nobody has claimed scores 0.
    """

    name: str = "Usage Count Rule"
    description: str = (
        "Score based on how many people say they use or have favorited the "
        "package, whichever is higher, log scaled: 10 are 7 points, 100 are 14, "
        "1,000 or more are 20. At least 1 for any package with a release or "
        "commit in the last three years"
    )
    max_score: int = 20
    documentation_url: str = f"{settings.DOCS_URL}/rules/#searchv3.rules.UsageCountRule"

    points_per_decade: int = 7
    floor_points: int = 1
    maintained_years: int = 3

    def _points(self, count: int) -> int:
        if count <= 0:
            return 0
        points = math.log10(count) * self.points_per_decade
        return int(min(max(points, self.floor_points), self.max_score))

    def check(self, package: Package) -> CheckResult:
        # `score_package` querysets annotate `usage_count` and
        # `favorites_count`; fall back to queries for a bare instance.
        usage_count = getattr(package, "usage_count", None)
        if usage_count is None:
            usage_count = package.usage.count()
        favorites_count = getattr(package, "favorites_count", None)
        if favorites_count is None:
            favorites_count = package.favorite_set.count()

        if usage_count or favorites_count:
            users = f"{usage_count:,} {'person says' if usage_count == 1 else 'people say'} they use the package"
            favs = f"{favorites_count:,} favorited it"
            return CheckResult(
                score=max(self._points(usage_count), self._points(favorites_count)),
                message=f"{users}, {favs}.",
            )
        age = package.activity_age
        if age is not None and age.days < 365 * self.maintained_years:
            return CheckResult(
                score=self.floor_points,
                message=(
                    "Nobody has said they use or favorited the package yet; one "
                    "point for a release or commit in the last three years."
                ),
            )
        return CheckResult(
            score=0, message="Nobody has said they use or favorited the package yet."
        )


GRADE_TEXT = {1.0: "still supported", 0.5: "near end of life", 0.0: "end of life"}


class VersionSupportRule(ScoreRule):
    """Points for claiming Python and Django versions that are still supported.

    Each of Python and Django is graded on the best version the package
    claims: 1.0 for one that is still supported, 0.5 for one in extended
    support or the newest end-of-life one, 0.0 for older. The two grades
    are averaged. A package with no Python or Django version data is left
    out of the total instead of scoring 0.
    """

    name: str = "Version Support Rule"
    description: str = (
        "Check if the package supports Python and Django versions that are "
        "still supported. Packages with no version data are left out"
    )
    max_score: int = 20
    documentation_url: str = (
        f"{settings.DOCS_URL}/rules/#searchv3.rules.VersionSupportRule"
    )

    def check(self, package: Package) -> CheckResult:
        support = version_support(package)
        parts = []
        for label, slug, cycles in (
            ("Python", "python", support.python),
            ("Django", "django", support.django),
        ):
            grade = support_grade(slug, cycles) if cycles else None
            if grade is not None:
                parts.append((label, grade))

        if not parts:
            return CheckResult(
                score=0,
                skipped=True,
                message="No Python or Django version data, so this check is left out.",
            )

        score = round(self.max_score * sum(grade for _, grade in parts) / len(parts))
        message = " ".join(f"{label}: {GRADE_TEXT[grade]}." for label, grade in parts)
        return CheckResult(score=score, message=message)


class WatchersRule(ScoreRule):
    """Points for repository stars, on a log scale.

    Five points per tenfold: 10 stars are 5, 100 are 10, 1,000 are 15,
    10,000 or more are 20. Linear, as before, gave full marks to every
    repository with 20 stars, which was half the catalogue, so the rule
    could not tell a 20-star package from a 20,000-star one.
    """

    name: str = "Watchers Rule"
    description: str = (
        "Score based on repository stars, log scaled: 10 stars are 5 points, "
        "100 are 10, 1,000 are 15, 10,000 are 20"
    )
    max_score: int = 20
    documentation_url: str = f"{settings.DOCS_URL}/rules/#searchv3.rules.WatchersRule"

    points_per_decade: int = 5

    def check(self, package: Package) -> CheckResult:
        if package.repo_watchers:
            score = log_points(
                package.repo_watchers, self.points_per_decade, self.max_score
            )
            return CheckResult(
                score=score,
                message=f"Package repository has {package.repo_watchers:,} stars.",
            )
        return CheckResult(
            score=0, message="No watchers data for the package repository."
        )


def calc_package_weight(
    *, package: Package, rules: list[ScoreRule], max_score: int
) -> dict:
    total_score = 0
    max_possible_score = 0
    breakdown = []
    messages = []
    factor = 1.0

    for rule in rules:
        result = rule.check(package=package)
        total_score += result.score
        factor *= result.factor
        # A skipped rule has nothing to read, so its points leave the
        # total too instead of counting as zero.
        rule_max = 0 if result.skipped else rule.max_score
        max_possible_score += rule_max
        messages.append(result.message)
        breakdown.append(
            {
                "rule": rule.name,
                "description": rule.description,
                "score": result.score,
                "max_score": rule_max,
                "message": result.message,
                "documentation_url": rule.documentation_url,
            }
        )

    # Integer arithmetic: 57 / 100 * 100 is 56.999 in floating point, and
    # int() of that is 56.
    normalized_score = (
        total_score * max_score // max_possible_score if max_possible_score > 0 else 0
    )

    return {
        "total_score": int(normalized_score * factor),
        "message": " ".join(messages),
        "breakdown": breakdown,
        "factor": factor,
    }


# The checks that make up `Package.score`, in the order the score page
# lists them. The activity factor first, then eight rules at 20 points
# each, up to 160 scaled to 100 and multiplied by the factor.
PACKAGE_RULES: list[ScoreRule] = [
    ActivityRule(),
    DeprecatedRule(),
    DescriptionRule(),
    DocumentationRule(),
    DownloadsRule(),
    ForkRule(),
    UsageCountRule(),
    VersionSupportRule(),
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
