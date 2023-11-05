from time import gmtime, strftime

import djclick as click
import json
from django.conf import settings
from rich import print

from core.utils import healthcheck
from searchv2.builders import build_1
from searchv2.rules import *
from package.models import Package


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
        documentation_url="https://docs.yoursite.com/rules/groups/activity",
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
