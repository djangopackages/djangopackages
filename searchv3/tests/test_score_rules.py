from django.test import TestCase
from django.utils import timezone
from model_bakery import baker

from searchv3.builders import calc_grid_weight
from searchv3.rules import (
    DeprecatedRule,
    DescriptionRule,
    DownloadsRule,
    ForkRule,
    RecentReleaseRule,
    WatchersRule,
    calc_package_weight,
)

RULES = [
    DeprecatedRule(),
    DescriptionRule(),
    DownloadsRule(),
    ForkRule(),
    WatchersRule(),
]


class CalcPackageWeightTest(TestCase):
    def _score(self, **overrides) -> int:
        defaults = {
            "date_deprecated": None,
            "pypi_downloads": 20,
            "repo_description": "A package description",
            "repo_forks": 20,
            "repo_watchers": 20,
        }
        defaults.update(overrides)
        package = baker.make("package.Package", **defaults)
        result = calc_package_weight(package=package, rules=RULES, max_score=100)
        return result["total_score"]

    def test_baseline(self):
        self.assertEqual(self._score(), 80)

    def test_deprecated_deduction(self):
        self.assertEqual(self._score(date_deprecated=timezone.now()), 60)

    def test_no_description_deduction(self):
        self.assertEqual(self._score(repo_description=""), 60)

    def test_no_watchers_deduction(self):
        self.assertEqual(self._score(repo_watchers=0), 60)

    def test_no_forks_deduction(self):
        self.assertEqual(self._score(repo_forks=0), 60)

    def test_high_downloads_bonus(self):
        self.assertEqual(self._score(pypi_downloads=20_000), 100)

    def test_medium_downloads_bonus(self):
        self.assertEqual(self._score(pypi_downloads=10_000), 90)

    def test_low_downloads_bonus(self):
        self.assertEqual(self._score(pypi_downloads=1_000), 81)


class CalcGridWeightTest(TestCase):
    def test_locked_with_header_and_packages(self):
        grid = baker.make("grid.Grid", is_locked=True, header=True)
        grid.packages.add(baker.make("package.Package"))
        self.assertEqual(calc_grid_weight(grid=grid, max_weight=120), 100)

    def test_unlocked_deducts(self):
        grid = baker.make("grid.Grid", is_locked=False, header=True)
        grid.packages.add(baker.make("package.Package"))
        self.assertEqual(calc_grid_weight(grid=grid, max_weight=120), 80)

    def test_no_header_deducts(self):
        grid = baker.make("grid.Grid", is_locked=True, header=False)
        grid.packages.add(baker.make("package.Package"))
        self.assertEqual(calc_grid_weight(grid=grid, max_weight=120), 80)

    def test_no_packages_deducts(self):
        grid = baker.make("grid.Grid", is_locked=True, header=True)
        self.assertEqual(calc_grid_weight(grid=grid, max_weight=120), 80)

    def test_all_penalties(self):
        grid = baker.make("grid.Grid", is_locked=False, header=False)
        self.assertEqual(calc_grid_weight(grid=grid, max_weight=120), 40)

    def test_custom_max_weight(self):
        grid = baker.make("grid.Grid", is_locked=True, header=True)
        grid.packages.add(baker.make("package.Package"))
        self.assertEqual(calc_grid_weight(grid=grid, max_weight=60), 50)


class RecentReleaseRuleTest(TestCase):
    def test_handles_null_upload_time(self):
        category = baker.make("package.Category")
        package = baker.make("package.Package", category=category)
        version = baker.make("package.Version", package=package, upload_time=None)
        package.latest_version = version
        package.save(update_fields=["latest_version"])

        result = RecentReleaseRule().check(package=package)

        self.assertEqual(result.score, 0)
        self.assertEqual(result.message, "No release data found for the package.")

    def test_scores_recent_release(self):
        category = baker.make("package.Category")
        package = baker.make("package.Package", category=category)
        version = baker.make(
            "package.Version",
            package=package,
            upload_time=timezone.now() - timezone.timedelta(days=30),
        )
        package.latest_version = version
        package.save(update_fields=["latest_version"])

        result = RecentReleaseRule().check(package=package)

        self.assertEqual(result.score, RecentReleaseRule().max_score)
        self.assertEqual(result.message, "Last release is less than a year old.")
