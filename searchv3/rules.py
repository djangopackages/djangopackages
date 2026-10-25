from datetime import timedelta

from django.conf import settings
from django.utils import timezone
from pydantic import BaseModel

from package.models import Package


class CheckResult(BaseModel):
    score: int
    message: str


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


class DeprecatedRule(ScoreRule):
    name: str = "Deprecated Rule"
    description: str = "Check if the package is deprecated"
    max_score: int = 20
    documentation_url: str = f"{settings.DOCS_URL}/rules/#searchv3.rules.DeprecatedRule"

    def check(self, package: Package) -> CheckResult:
        if not package.is_deprecated:
            return CheckResult(
                score=self.max_score, message="Package is not deprecated."
            )
        return CheckResult(score=0, message="Package is deprecated.")


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
    name: str = "Downloads Rule"
    description: str = "Score based on the number of PyPi downloads"
    max_score: int = 20
    documentation_url: str = f"{settings.DOCS_URL}/rules/#searchv3.rules.DownloadsRule"

    def check(self, package: Package) -> CheckResult:
        if package.pypi_downloads:
            score = min(int(package.pypi_downloads / 1_000), self.max_score)
            return CheckResult(
                score=score,
                message=f"Package has {package.pypi_downloads} PyPi downloads.",
            )
        return CheckResult(score=0, message="No PyPi downloads data for the package.")


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


class LastUpdatedRule(ScoreRule):
    name: str = "Last Updated Rule"
    description: str = "Score based on how recently the package was last updated"
    max_score: int = 20
    documentation_url: str = (
        f"{settings.DOCS_URL}/rules/#searchv3.rules.LastUpdatedRule"
    )

    def check(self, package: Package) -> CheckResult:
        try:
            last_updated = package.last_commit_date
            now = timezone.now()

            if last_updated:
                if (now - last_updated) < timedelta(90):
                    return CheckResult(
                        score=self.max_score,
                        message="Package was updated less than 3 months ago.",
                    )
                if (now - last_updated) < timedelta(182):
                    return CheckResult(
                        score=int(self.max_score / 2),
                        message="Package was updated less than 6 months ago.",
                    )
                if (now - last_updated) < timedelta(365):
                    return CheckResult(
                        score=int(self.max_score / 4),
                        message="Package was updated less than 1 year ago.",
                    )
                return CheckResult(
                    score=0, message="Package was updated more than 1 year ago."
                )

            return CheckResult(score=0, message="No update data found for the package.")

        except AttributeError:
            return CheckResult(score=0, message="No update data found for the package.")


class RecentReleaseRule(ScoreRule):
    name: str = "Recent Release Rule"
    description: str = "Score if the last release is less than a year old"
    max_score: int = 20
    documentation_url: str = (
        f"{settings.DOCS_URL}/rules/#searchv3.rules.RecentReleaseRule"
    )

    def check(self, package: Package) -> CheckResult:
        last_released = package.latest_version
        if not last_released or not last_released.upload_time:
            return CheckResult(
                score=0, message="No release data found for the package."
            )

        now = timezone.now()
        if now - last_released.upload_time < timedelta(365):
            return CheckResult(
                score=self.max_score,
                message="Last release is less than a year old.",
            )

        return CheckResult(score=0, message="Last release is more than a year old.")


class UsageCountRule(ScoreRule):
    name: str = "Usage Count Rule"
    description: str = "Score based on the usage count"
    max_score: int = 20
    documentation_url: str = f"{settings.DOCS_URL}/rules/#searchv3.rules.UsageCountRule"

    def check(self, package: Package) -> CheckResult:
        usage_count = package.usage.count()
        if usage_count:
            score = min(usage_count, self.max_score)
            return CheckResult(
                score=score, message=f"Package has a usage count of {usage_count}."
            )
        return CheckResult(score=0, message="No usage data found for the package.")


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

    for rule in rules:
        result = rule.check(package=package)
        total_score += result.score
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
        "total_score": int(normalized_score),
        "message": " ".join(messages),
        "breakdown": breakdown,
    }
