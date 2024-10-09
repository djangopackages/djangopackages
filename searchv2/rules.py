from datetime import timedelta
from django.utils import timezone
from pydantic import BaseModel

from package.models import Package
from django.conf import settings


class CheckResult(BaseModel):
    """
    Model to store the result of a check, which includes the score and a message.
    """

    score: int
    message: str


class ScoreRule(BaseModel):
    """
    Abstract base class for all score rules. It validates the input data using Pydantic,
    and requires a `check` method that should be implemented by subclasses.

    Attributes:
        name: The name of the score rule.
        description: The description of the score rule.
        max_score: The maximum score that can be awarded by this rule.
        documentation_url: An optional URL to the documentation for this rule.
        # rules: An optional list of sub-rules.

    Methods:
        check: Checks the given package against this scoring rule and returns a score.
    """

    name: str
    description: str
    max_score: int
    documentation_url: str | None = None
    # rules: Optional[List["ScoreRule"]] = None

    class Config:
        """
        Config class for ScoreRule.
        Enables validation on assignment.
        """

        validate_assignment = True

    def check(self, package: Package) -> CheckResult:
        """
        Checks the given package against this scoring rule and returns a CheckResult(score, message).
        This method should be implemented by subclasses.

        Args:
            package: The package to check.

        Raises:
            NotImplementedError: If this method is not implemented by a subclass.
        """
        raise NotImplementedError("Subclasses should implement this!")


class ScoreRuleGroup(ScoreRule):
    """
    A group of rules, which checks a package by applying each rule in the group,
    and returns a normalized total score and a combined message from all checks.

    Attributes:
        rules: A list of ScoreRule objects in this group.

    Methods:
        check: Checks the given package against each scoring rule in this group, and returns a CheckResult instance
               with the normalized total score and a combined message.
    """

    rules: list[ScoreRule]

    def check(self, package: Package) -> CheckResult:
        """
        Checks the given package against each scoring rule in this group, and returns a CheckResult instance
        with the normalized total score and a combined message.

        The total score is calculated by summing up the scores from each rule.
        It is then normalized by dividing it by the sum of maximum scores of all the rules in the group, and multiplying
        by the maximum score of this group.

        If the sum of the maximum scores of all the rules in the group is zero, the normalized total score is set to zero.

        Args:
            package: The package to check.

        Returns:
            A CheckResult instance with the normalized total score and a combined message from all checks.
        """
        results = [rule.check(package=package) for rule in self.rules]
        total_score = sum(result.score for result in results)
        max_possible_score = sum(rule.max_score for rule in self.rules)

        # Normalize the total score to the max score of this group.
        normalized_score = (
            (total_score / max_possible_score) * self.max_score
            if max_possible_score > 0
            else 0
        )

        # Combine all the messages from the checks.
        messages = [result.message for result in results]

        return CheckResult(score=int(normalized_score), message=" ".join(messages))


class DeprecatedRule(ScoreRule):
    """
    A specific rule that checks if the package is deprecated.
    """

    name: str = "Deprecated Rule"
    description: str = "Check if the package is deprecated"
    max_score: int = 20
    documentation_url: str = f"{settings.DOCS_URL}/rules/deprecated"

    def check(self, package: Package) -> CheckResult:
        """
        Check if the package is deprecated.
        Returns a full score and a success message if the package is not deprecated,
        or a zero score and an error message otherwise.
        """
        if not package.is_deprecated:
            return CheckResult(
                score=self.max_score, message="Package is not deprecated."
            )
        else:
            return CheckResult(score=0, message="Package is deprecated.")


class FavoritePackageRule(ScoreRule):
    """
    A specific rule that checks if the package is favorite.
    """

    name: str = "Favorite Package Rule"
    description: str = "Check if the package is favorite"
    max_score: int = 20
    documentation_url: str = f"{settings.DOCS_URL}/rules/favorite-package"

    def check(self, package: Package) -> CheckResult:
        """
        Check if the package is favorite.
        Returns a full score and a success message if the package is not favorite,
        or a zero score and an error message otherwise.
        """
        if package.has_favorite:
            return CheckResult(score=self.max_score, message="Package is favorite.")
        else:
            return CheckResult(score=0, message="Package is not favorite.")


class DescriptionRule(ScoreRule):
    """
    A specific rule that checks if the package has a description.
    """

    name: str = "Description Rule"
    description: str = "Check if the package has a description"
    max_score: int = 20
    documentation_url: str = f"{settings.DOCS_URL}/rules/description"

    def check(self, package: Package) -> CheckResult:
        """
        Check if the package has a description.
        Returns a full score and a success message if the package has a description,
        or a zero score and an error message otherwise.
        """
        if package.repo_description and package.repo_description.strip():
            return CheckResult(
                score=self.max_score, message="Package has a description."
            )
        else:
            return CheckResult(score=0, message="Package has no description.")


class DocumentationRule(ScoreRule):
    """
    A specific rule that checks for the presence of documentation in a package.
    """

    name: str = "Documentation Rule"
    description: str = "Check if the package has a documentation URL"
    max_score: int = 20

    def check(self, package: Package) -> CheckResult:
        """
        Check if the package has a documentation URL.
        Returns a full score and a success message if the documentation exists,
        or a zero score and an error message otherwise.
        """
        if package.documentation_url:
            return CheckResult(score=self.max_score, message="Documentation exists.")
        else:
            return CheckResult(score=0, message="No documentation.")


class DownloadsRule(ScoreRule):
    """
    A specific rule that scores based on the number of PyPi downloads.
    """

    name: str = "Downloads Rule"
    description: str = "Score based on the number of PyPi downloads"
    max_score: int = 20
    documentation_url: str = f"{settings.DOCS_URL}/rules/downloads"

    def check(self, package: Package) -> CheckResult:
        """
        Check the number of PyPi downloads for the package.
        Returns a score and a success message based on the number of downloads,
        or a zero score and an error message if no downloads data is found.
        """
        if package.pypi_downloads:
            score = min(int(package.pypi_downloads / 1_000), self.max_score)
            return CheckResult(
                score=score,
                message=f"Package has {package.pypi_downloads} PyPi downloads.",
            )
        else:
            return CheckResult(
                score=0, message="No PyPi downloads data for the package."
            )


class ForkRule(ScoreRule):
    """
    A specific rule that scores based on the number of repository forks.
    """

    name: str = "Fork Rule"
    description: str = "Score based on the number of forks"
    max_score: int = 20
    documentation_url: str = f"{settings.DOCS_URL}/rules/fork"

    def check(self, package: Package) -> CheckResult:
        """
        Check the number of forks for the package's repository.
        Returns a score and a success message based on the number of forks,
        or a zero score and an error message if no forks data is found.
        """
        if package.repo_forks:
            score = min(package.repo_forks, self.max_score)
            return CheckResult(
                score=score,
                message=f"Package repository has {package.repo_forks} forks.",
            )
        else:
            return CheckResult(
                score=0, message="No forks data for the package repository."
            )


class LastUpdatedRule(ScoreRule):
    """
    A specific rule that scores based on how recently the package was last updated.
    """

    name: str = "Last Updated Rule"
    description: str = "Score based on how recently the package was last updated"
    max_score: int = 20

    def check(self, package: Package) -> CheckResult:
        """
        Check how recently the package was last updated.
        Returns a score and a success message based on the update recency,
        or a zero score and an error message if no update data is found or an error occurs.
        """
        try:
            last_updated = package.last_updated()
            now = timezone.now()

            if last_updated:
                if (now - last_updated) < timedelta(90):  # less than 3 months
                    return CheckResult(
                        score=self.max_score,
                        message="Package was updated less than 3 months ago.",
                    )
                elif (now - last_updated) < timedelta(182):  # less than 6 months
                    return CheckResult(
                        score=int(self.max_score / 2),
                        message="Package was updated less than 6 months ago.",
                    )
                elif (now - last_updated) < timedelta(365):  # less than 1 year
                    return CheckResult(
                        score=int(self.max_score / 4),
                        message="Package was updated less than 1 year ago.",
                    )
                else:
                    return CheckResult(
                        score=0, message="Package was updated more than 1 year ago."
                    )

            return CheckResult(score=0, message="No update data found for the package.")

        except AttributeError:
            return CheckResult(score=0, message="No update data found for the package.")


class RecentReleaseRule(ScoreRule):
    """
    A specific rule that scores based on whether the last release is less than a year old.
    """

    name: str = "Recent Release Rule"
    description: str = "Score if the last release is less than a year old"
    max_score: int = 20

    def check(self, package: Package) -> CheckResult:
        """
        Check if the last release of the package is less than a year old.
        Returns a full score and a success message if the last release is recent,
        or a zero score and an error message otherwise.
        """
        try:
            last_released = package.last_released()
            now = timezone.now()
            if now - last_released.upload_time < timedelta(365):
                return CheckResult(
                    score=self.max_score,
                    message="Last release is less than a year old.",
                )
            else:
                return CheckResult(
                    score=0, message="Last release is more than a year old."
                )
        except AttributeError:
            return CheckResult(
                score=0, message="No release data found for the package."
            )


class UsageCountRule(ScoreRule):
    """
    A specific rule that scores based on the usage count of the package.
    """

    name: str = "Usage Count Rule"
    description: str = "Score based on the usage count"
    max_score: int = 20
    documentation_url: str = f"{settings.DOCS_URL}/rules/usage_count"

    def check(self, package: Package) -> CheckResult:
        """
        Check the usage count of the package.
        Returns a score and a success message based on the usage count,
        or a zero score and an error message if no usage data is found.
        """
        usage_count = package.usage.count()
        if usage_count:
            score = min(usage_count, self.max_score)
            return CheckResult(
                score=score, message=f"Package has a usage count of {usage_count}."
            )
        else:
            return CheckResult(score=0, message="No usage data found for the package.")


class WatchersRule(ScoreRule):
    """
    A specific rule that scores based on the number of watchers of the package's repository.
    """

    name: str = "Watchers Rule"
    description: str = "Score based on the number of watchers"
    max_score: int = 20
    documentation_url: str = f"{settings.DOCS_URL}/rules/watchers"

    def check(self, package: Package) -> CheckResult:
        """
        Check the number of watchers for the package's repository.
        Returns a score and a success message based on the number of watchers,
        or a zero score and an error message if no watchers data is found.
        """
        if package.repo_watchers:
            score = min(package.repo_watchers, self.max_score)
            return CheckResult(
                score=score,
                message=f"Package repository has {package.repo_watchers} watchers.",
            )
        else:
            return CheckResult(
                score=0, message="No watchers data for the package repository."
            )


def calc_package_weight(
    *, package: Package, rules: list[ScoreRule], max_score: int
) -> dict:
    """
    Calculates the normalized total score of a given package based on a list of scoring rules.

    Args:
        package: The package to be evaluated.
        rules: A list of scoring rules to be applied to the package.
        max_score: The maximum possible score.

    Returns:
        A dictionary containing the total normalized score, a combined message, and a breakdown of scores from each rule.
        The breakdown is a list of dictionaries, each containing the name, description, score, max score, message, and
        documentation URL of each rule.
    """
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
