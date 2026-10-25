import uuid

from django.test import TestCase
from django.utils import timezone
from model_bakery import baker

from searchv3.builders import calc_grid_weight
from searchv3.rules import (
    PACKAGE_RULES,
    DeprecatedRule,
    DormantRule,
    DescriptionRule,
    DownloadsRule,
    ForkRule,
    RecentReleaseRule,
    UsageCountRule,
    WatchersRule,
    calc_package_weight,
    score_package,
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

    def test_archived_deduction(self):
        self.assertEqual(self._score(date_repo_archived=timezone.now()), 60)


class DormantRuleTest(TestCase):
    def _package(self, **overrides):
        defaults = {
            "repo_watchers": 500,
            "repo_forks": 50,
            "repo_description": "x",
            # repo_url is unique; two blank ones in one test collide.
            "repo_url": f"https://github.com/t/{uuid.uuid4().hex[:8]}",
        }
        defaults.update(overrides)
        return baker.make("package.Package", **defaults)

    def test_recent_commit_is_not_dormant(self):
        package = self._package(
            last_commit_date=timezone.now() - timezone.timedelta(days=700)
        )
        result = DormantRule().check(package=package)
        self.assertFalse(result.zero_score)
        self.assertFalse(package.is_dormant)

    def test_three_idle_years_is_dormant(self):
        when = timezone.now() - timezone.timedelta(days=365 * 3 + 1)
        package = self._package(last_commit_date=when)
        result = DormantRule().check(package=package)
        self.assertTrue(result.zero_score)
        self.assertEqual(package.dormant_since, when)
        self.assertIn(f"no commit since {when:%B %Y}", result.message)

    def test_recent_release_keeps_an_old_repo_awake(self):
        package = self._package(
            last_commit_date=timezone.now() - timezone.timedelta(days=365 * 4)
        )
        version = baker.make(
            "package.Version",
            package=package,
            upload_time=timezone.now() - timezone.timedelta(days=100),
        )
        package.latest_version = version
        package.save(update_fields=["latest_version"])
        self.assertFalse(package.is_dormant)
        self.assertFalse(DormantRule().check(package=package).zero_score)

    def test_old_release_is_dormant_even_with_recent_commits(self):
        # django-jet: commits in 2025, last PyPI release 2018.
        released = timezone.now() - timezone.timedelta(days=365 * 7)
        package = self._package(
            last_commit_date=timezone.now() - timezone.timedelta(days=30)
        )
        version = baker.make("package.Version", package=package, upload_time=released)
        package.latest_version = version
        package.save(update_fields=["latest_version"])
        result = DormantRule().check(package=package)
        self.assertTrue(result.zero_score)
        self.assertEqual(package.dormant_since, released)
        self.assertIn("No release since", result.message)

    def test_not_on_pypi_is_judged_on_commits(self):
        package = self._package(
            last_commit_date=timezone.now() - timezone.timedelta(days=30)
        )
        self.assertFalse(package.is_dormant)
        result = DormantRule().check(
            package=self._package(
                last_commit_date=timezone.now() - timezone.timedelta(days=365 * 4)
            )
        )
        self.assertTrue(result.zero_score)
        self.assertIn("Not on PyPI and no commit since", result.message)

    def test_no_dates_at_all_is_dormant(self):
        package = self._package(last_commit_date=None)
        result = DormantRule().check(package=package)
        self.assertTrue(result.zero_score)
        self.assertIsNone(package.dormant_since)
        self.assertIn("No release or commit date on record", result.message)

    def test_dormant_zeroes_the_whole_score(self):
        package = self._package(
            last_commit_date=timezone.now() - timezone.timedelta(days=365 * 5),
            pypi_downloads=50_000,
        )
        result = score_package(package)
        self.assertEqual(result["total_score"], 0)
        self.assertTrue(result["zeroed"])
        # The point rules still report what they would have earned.
        self.assertEqual(sum(item["score"] for item in result["breakdown"]), 100)


class ScorePackageTest(TestCase):
    """`score_package` is `Package.score`: a gate plus eight rules, 20 points each."""

    def test_gate_plus_eight_rules_scaled_to_100(self):
        self.assertEqual(len(PACKAGE_RULES), 9)
        self.assertIsInstance(PACKAGE_RULES[0], DormantRule)
        self.assertEqual(sum(rule.max_score for rule in PACKAGE_RULES), 160)

    def test_fresh_100_stars_nothing_else(self):
        package = baker.make(
            "package.Package",
            repo_watchers=100,
            repo_description="",
            repo_forks=0,
            pypi_downloads=0,
            last_commit_date=timezone.now(),
        )
        result = score_package(package)
        # not deprecated 20 + updated 20 + watchers 20 = 60 of 160.
        self.assertEqual(result["total_score"], 37)
        self.assertEqual(
            [item["rule"] for item in result["breakdown"]],
            [rule.name for rule in PACKAGE_RULES],
        )

    def test_usage_count_annotation_is_used(self):
        package = baker.make("package.Package")
        package.usage_count = 7
        self.assertEqual(UsageCountRule().check(package=package).score, 7)


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
