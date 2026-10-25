import uuid

from django.test import TestCase
from django.utils import timezone
from model_bakery import baker

from searchv3.builders import calc_grid_weight
from searchv3.rules import (
    PACKAGE_RULES,
    DeprecatedRule,
    ActivityRule,
    DescriptionRule,
    DownloadsRule,
    ForkRule,
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
            "pypi_downloads": 10,
            "repo_description": "A package description",
            "repo_forks": 20,
            "repo_watchers": 20,
            # repo_url is unique; several packages in one test collide.
            "repo_url": f"https://github.com/t/{uuid.uuid4().hex[:8]}",
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

    def test_downloads_log_scale(self):
        # 4 points per tenfold above 10 a month, capped at 20.
        for downloads, expected in [
            (10, 80),
            (100, 84),
            (286, 85),
            (1_000, 88),
            (10_000, 92),
            (100_000, 96),
            (1_000_000, 100),
            (5_000_000, 100),
        ]:
            with self.subTest(downloads=downloads):
                self.assertEqual(self._score(pypi_downloads=downloads), expected)

    def test_no_downloads_data(self):
        self.assertEqual(self._score(pypi_downloads=0), 80)

    def test_archived_deduction(self):
        self.assertEqual(self._score(date_repo_archived=timezone.now()), 60)


class ActivityRuleTest(TestCase):
    def _package(self, **overrides):
        defaults = {
            "repo_watchers": 500,
            "repo_forks": 50,
            "repo_description": "x",
            "pypi_downloads": 0,
            # repo_url is unique; two blank ones in one test collide.
            "repo_url": f"https://github.com/t/{uuid.uuid4().hex[:8]}",
        }
        defaults.update(overrides)
        return baker.make("package.Package", **defaults)

    def _released(self, package, when):
        version = baker.make("package.Version", package=package, upload_time=when)
        package.latest_version = version
        package.save(update_fields=["latest_version"])

    def test_first_year_is_full_score(self):
        package = self._package(
            last_commit_date=timezone.now() - timezone.timedelta(days=300)
        )
        self.assertEqual(package.activity_factor, 1.0)
        result = ActivityRule().check(package=package)
        self.assertEqual(result.factor, 1.0)
        self.assertIn("within the last year: full score", result.message)

    def test_halves_every_eighteen_months_after_the_first_year(self):
        for years, expected in [(1, 1.0), (2.5, 0.5), (4, 0.25), (5.5, 0.125)]:
            with self.subTest(years=years):
                package = self._package(
                    last_commit_date=timezone.now()
                    - timezone.timedelta(days=int(365 * years) + 1)
                )
                self.assertAlmostEqual(package.activity_factor, expected, places=2)

    def test_old_commit_scales_the_message_and_score(self):
        when = timezone.now() - timezone.timedelta(days=365 * 4)
        package = self._package(last_commit_date=when)
        result = ActivityRule().check(package=package)
        self.assertAlmostEqual(result.factor, 0.25, places=2)
        self.assertIn(f"Last commit {when:%B %Y}, 4 years ago", result.message)
        self.assertIn("scaled to 25%", result.message)

    def test_release_dates_a_package_on_pypi(self):
        # django-jet: commits in 2025, last PyPI release 2018.
        released = timezone.now() - timezone.timedelta(days=365 * 7)
        package = self._package(
            pypi_url="https://pypi.org/project/django-jet/",
            last_commit_date=timezone.now() - timezone.timedelta(days=30),
        )
        self._released(package, released)
        self.assertTrue(package.release_dates_it)
        self.assertEqual(package.last_activity, released)
        self.assertLess(package.activity_factor, 0.07)
        self.assertIn("Last release", ActivityRule().check(package=package).message)

    def test_recent_release_keeps_an_old_repo_at_full_score(self):
        package = self._package(
            pypi_url="https://pypi.org/project/x/",
            last_commit_date=timezone.now() - timezone.timedelta(days=365 * 4),
        )
        self._released(package, timezone.now() - timezone.timedelta(days=100))
        self.assertEqual(package.activity_factor, 1.0)

    def test_no_pypi_link_is_dated_by_commits_despite_old_releases(self):
        # sentry: old PyPI releases on record, PyPI link cleared, commits daily.
        package = self._package(
            pypi_url="",
            last_commit_date=timezone.now() - timezone.timedelta(days=1),
        )
        self._released(package, timezone.now() - timezone.timedelta(days=365 * 4))
        self.assertFalse(package.on_pypi)
        self.assertFalse(package.release_dates_it)
        self.assertEqual(package.activity_factor, 1.0)

    def test_no_dates_at_all_is_zero(self):
        package = self._package(last_commit_date=None)
        self.assertEqual(package.activity_factor, 0.0)
        result = ActivityRule().check(package=package)
        self.assertEqual(result.factor, 0.0)
        self.assertIn("No release or commit date on record", result.message)

    def test_factor_multiplies_the_whole_score(self):
        package = self._package(
            last_commit_date=timezone.now() - timezone.timedelta(days=365 * 4),
            pypi_downloads=100_000,
        )
        result = score_package(package)
        # not deprecated 20, description 20, downloads 16, forks 20, watchers 20
        # = 96 of 120 = 80, then a quarter of that at four years.
        self.assertEqual(sum(item["score"] for item in result["breakdown"]), 96)
        self.assertAlmostEqual(result["factor"], 0.25, places=2)
        self.assertEqual(result["total_score"], 20)

    def test_age_text(self):
        for days, text in [
            (20, "under a month"),
            (400, "1 year 1 month"),
            (365 * 2 + 180, "2 years 6 months"),
            (365 * 4, "4 years"),
        ]:
            with self.subTest(days=days):
                package = self._package(
                    last_commit_date=timezone.now() - timezone.timedelta(days=days)
                )
                self.assertEqual(package.activity_age_text, text)


class ScorePackageTest(TestCase):
    """`score_package` is `Package.score`: the activity factor plus six rules, 20 points each."""

    def test_factor_plus_six_rules_scaled_to_100(self):
        self.assertEqual(len(PACKAGE_RULES), 7)
        self.assertIsInstance(PACKAGE_RULES[0], ActivityRule)
        self.assertEqual(sum(rule.max_score for rule in PACKAGE_RULES), 120)

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
        # not deprecated 20 + watchers 20 = 40 of 120.
        self.assertEqual(result["total_score"], 33)
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
