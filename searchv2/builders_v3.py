import json

from datetime import timedelta
from django.utils import timezone
from rich import print

from grid.models import Grid
from package.models import Commit, Package
from searchv2.models import SearchV2
from searchv2.rules import calc_package_weight
from searchv2.rules import DeprecatedRule
from searchv2.rules import DescriptionRule
from searchv2.rules import DownloadsRule
from searchv2.rules import ForkRule
from searchv2.rules import LastUpdatedRule
from searchv2.rules import RecentReleaseRule
from searchv2.rules import UsageCountRule
from searchv2.rules import WatchersRule
from searchv2.utils import clean_title
from searchv2.utils import remove_prefix


def build_1(*, verbose: bool = False):
    last_week = timezone.now() - timedelta(7)

    SearchV2.objects.filter(created__lte=last_week).delete()

    index_packages(verbose=verbose)
    index_groups(verbose=verbose)

    return SearchV2.objects.all()


def index_packages(*, verbose: bool = False):
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

    # demo the group rule

    # group = ScoreRuleGroup(
    #     name="Activity Rules",
    #     description="Rules related to the package's recent activity",
    #     max_score=40,
    #     documentation_url="https://docs.yoursite.com/rules/groups/activity",
    #     rules=[LastUpdatedRule(), RecentReleaseRule()],
    # )

    # rules = [
    #     DeprecatedRule(),
    #     DescriptionRule(),
    #     DownloadsRule(),
    #     ForkRule(),
    #     UsageCountRule(),
    #     WatchersRule(),
    #     group,
    # ]

    # example of how to test it...
    # package = Package.objects.first()
    # package_score = calc_package_weight(package=package, rules=rules, max_score=100)
    # print(json.dumps(package_score, indent=2))

    for package in Package.objects.all().iterator():
        try:
            package_score = calc_package_weight(
                package=package, rules=rules, max_score=100
            )
            weight = package_score["total_score"]

            if verbose:
                print(f"{package.pk=}::{weight=}")
                print(json.dumps(package_score, indent=2))

            obj, created = SearchV2.objects.update_or_create(
                item_type="package",
                slug=package.slug,
                defaults={
                    "absolute_url": package.get_absolute_url(),
                    "category": package.category.title,
                    "clean_title": clean_title(remove_prefix(package.slug)),
                    "description": package.repo_description,
                    "participants": package.participants,
                    "pypi_downloads": package.pypi_downloads,
                    "repo_forks": package.repo_forks,
                    "repo_watchers": package.repo_watchers,
                    "slug_no_prefix": remove_prefix(package.slug),
                    "title": package.title,
                    "title_no_prefix": remove_prefix(package.title),
                    "usage": package.usage.count(),
                    "weight": weight,
                },
            )

            optional_save = False
            try:
                obj.last_committed = package.last_updated()
                optional_save = True
            except Commit.DoesNotExist:
                pass

            last_released = package.last_released()
            if last_released and last_released.upload_time:
                obj.last_released = last_released.upload_time
                optional_save = True

            if optional_save:
                obj.save()

        except Exception as e:
            print(f"[red]{e=}[/red]")


def calc_grid_weight(
    *,
    grid: Grid,
    max_weight: int = 120,
) -> int:
    increment = max_weight / 6

    weight = max_weight - increment

    if not grid.is_locked:
        weight -= increment

    if not grid.header:
        weight -= increment

    if not grid.packages.exists():
        weight -= increment

    return int(weight)


def index_groups(verbose: bool = False):
    max_weight = SearchV2.objects.only("weight").order_by("-weight").first()
    if max_weight:
        max_weight = max_weight.weight
    else:
        max_weight = 0

    if verbose:
        print(f"{max_weight=}")

    for grid in Grid.objects.all().iterator():
        try:
            weight = calc_grid_weight(grid=grid, max_weight=max_weight)

            if verbose:
                print(f"{grid.pk=}::{weight=}")

            obj, created = SearchV2.objects.update_or_create(
                item_type="grid",
                slug=grid.slug,
                defaults={
                    "absolute_url": grid.get_absolute_url(),
                    "clean_title": clean_title(remove_prefix(grid.slug)),
                    "description": grid.description,
                    "slug_no_prefix": remove_prefix(grid.slug),
                    "title": grid.title,
                    "title_no_prefix": remove_prefix(grid.title),
                    "weight": weight,
                },
            )
        except Exception as e:
            print(f"[red]{e=}[/red]")
