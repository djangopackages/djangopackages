from django.utils import timezone
from model_bakery import baker

from package.tests import initial_data
from searchv2.builders import build_1, calc_grid_weight, calc_package_weight
from searchv2.models import SearchV2


def test_build_1_count(db):
    initial_data.load()
    assert SearchV2.objects.count() == 0
    build_1()
    assert SearchV2.objects.count() == 6


def test_calc_grid_weight(db, faker):
    grid = baker.make("grid.Grid", header=True, is_locked=True)
    package = baker.make("package.Package")
    grid.packages.add(package)

    assert calc_grid_weight(grid=grid) == 100

    grid.header = False
    assert calc_grid_weight(grid=grid) == 80

    grid.is_locked = False
    assert calc_grid_weight(grid=grid) == 60

    grid.packages.remove(package)
    assert calc_grid_weight(grid=grid) == 40


def test_calc_package_weight(db, faker):
    package = baker.make(
        "package.Package",
        date_deprecated=None,
        documentation_url="https://",
        pypi_downloads=20,
        repo_description=faker.sentence(5),
        repo_forks=20,
        repo_watchers=20,
    )
    weight = calc_package_weight(package=package)
    assert weight == 80

    package.date_deprecated = timezone.now()
    assert calc_package_weight(package=package) == 20
    package.date_deprecated = None

    package.documentation_url = None
    assert calc_package_weight(package=package) == 60

    package.repo_description = None
    assert calc_package_weight(package=package) == 40

    package.repo_watchers = 0
    assert calc_package_weight(package=package) == 20

    package.repo_forks = 0
    assert calc_package_weight(package=package) == 0

    package.pypi_downloads = 20_000
    assert calc_package_weight(package=package) == 20

    package.pypi_downloads = 10_000
    assert calc_package_weight(package=package) == 10

    package.pypi_downloads = 1_000
    assert calc_package_weight(package=package) == 1

    package.pypi_downloads = 100
    assert calc_package_weight(package=package) == 0

    # TODO: package.usage.count()

    # TODO: package.last_updated()
    # three deltas for [20, 10, 5]

    # TODO: package.last_released()


def test_package_score_after_build(db):
    package = baker.make("package.Package", score=600)
    build_1()
    search_v2 = SearchV2.objects.get(item_type="package", slug=package.slug)
    assert search_v2.score == 600


def test_grid_score_is_zero_even_after_adding_a_package(db):
    package = baker.make("package.Package", score=600)
    grid = baker.make("grid.Grid")
    grid.packages.add(package)

    build_1()
    search_v2 = SearchV2.objects.get(item_type="grid", slug=grid.slug)
    assert search_v2.score == 0
