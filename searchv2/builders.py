from datetime import timedelta

from django.utils import timezone

from grid.models import Grid
from package.models import Commit, Package
from searchv2.models import SearchV2
from searchv2.utils import clean_title, remove_prefix


def build_1(*, verbose: bool = False):
    last_week = timezone.now() - timedelta(7)

    SearchV2.objects.filter(created__lte=last_week).delete()

    index_packages(verbose=verbose)
    index_groups(verbose=verbose)

    return SearchV2.objects.all()


def calc_package_weight(*, package: Package) -> int:
    now = timezone.now()

    weight = 0

    # does our package have documentation? (20 points)
    if package.documentation_url and len(package.documentation_url):
        weight += 20

    # is our package deprecated? (6 * 20 = 120 points)
    if not package.is_deprecated:
        if package.repo_description and package.repo_description.strip():
            weight += 20

        if package.repo_forks:
            weight += min(package.repo_forks, 20)

        if package.repo_watchers:
            weight += min(package.repo_watchers, 20)

        # PyPi downloads are always zero right now
        if package.pypi_downloads:
            weight += min(int(package.pypi_downloads / 1_000), 20)

        # based on our Version model
        if usage_count := package.usage.count():
            weight += min(usage_count, 20)

        # Is the last release less than a year old?
        try:
            if last_released := package.last_released():
                if now - last_released.upload_time < timedelta(365):
                    weight += 20
        except AttributeError:
            ...

    # Is there ongoing work or is this forgotten?
    if last_updated := package.last_updated():
        if (now - last_updated) < timedelta(90):
            weight += 20
        elif now - last_updated < timedelta(182):
            weight += 10
        elif now - last_updated < timedelta(365):
            weight += 5

    return weight


def index_packages(verbose: bool = False):
    for package in Package.objects.all().iterator():
        weight = calc_package_weight(package=package)

        if verbose:
            print(f"{package.pk=}::{weight=}")

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
                "score": package.score,
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
    max_weight = SearchV2.objects.only("weight").order_by("-weight").first().weight

    if verbose:
        print(f"{max_weight=}")

    for grid in Grid.objects.all().iterator():
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
