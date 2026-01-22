import djclick as click
import json
from rich import print

from package.models import Package
from searchv2.rules import calc_package_weight
from searchv2.rules import DeprecatedRule
from searchv2.rules import DescriptionRule
from searchv2.rules import DownloadsRule
from searchv2.rules import ForkRule
from searchv2.rules import LastUpdatedRule
from searchv2.rules import RecentReleaseRule
from searchv2.rules import ScoreRuleGroup
from searchv2.rules import UsageCountRule
from searchv2.rules import WatchersRule


@click.command()
@click.option("-v", "--verbose", is_flag=True, default=False)
def command(verbose):
    # demo default rules

    rules = [
        DeprecatedRule(),
        DescriptionRule(),
        DownloadsRule(),
        ForkRule(),
        LastUpdatedRule(),
        RecentReleaseRule(),
        UsageCountRule(),
        WatchersRule(),
    ]

    package = Package.objects.first()

    package_score = calc_package_weight(package=package, rules=rules, max_score=100)

    print(json.dumps(package_score, indent=2))

    # demo the group rule

    group = ScoreRuleGroup(
        name="Activity Rules",
        description="Rules related to the package's recent activity",
        max_score=40,
        documentation_url="https://docs.yoursite.com/rules/#searchv2.rules.ScoreRuleGroup",
        rules=[LastUpdatedRule(), RecentReleaseRule()],
    )

    rules = [
        DeprecatedRule(),
        DescriptionRule(),
        DownloadsRule(),
        ForkRule(),
        UsageCountRule(),
        WatchersRule(),
        group,
    ]

    package_score = calc_package_weight(package=package, rules=rules, max_score=100)

    print(json.dumps(package_score, indent=2))
