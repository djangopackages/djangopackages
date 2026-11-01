import datetime
from types import SimpleNamespace
from unittest import mock

from django.test import SimpleTestCase
from django.utils import timezone

from probes.version_support import support_grade
from searchv3.rules import (
    CheckResult,
    ScoreRule,
    VersionSupportRule,
    calc_package_weight,
)


def days(n: int) -> datetime.date:
    return timezone.now().date() + datetime.timedelta(days=n)


def build_lifecycle():
    """cycle: (release, eol, support), the shape `lifecycle` returns."""
    today = timezone.now().date()
    python = {
        "3.9": (days(-2000), days(-400), "false"),  # end of life, not the newest
        "3.10": (days(-1500), days(-30), "false"),  # newest end of life
        "3.11": (days(-1100), days(300), "false"),  # extended support only
        "3.12": (days(-700), days(900), "true"),  # supported
        "3.13": (days(-300), None, days(50).isoformat()),  # support ends later
        "3.14": (days(-200), None, days(-5).isoformat()),  # support date passed
        "3.15": (days(-50), None, None),  # no support info
    }
    django = {
        "3.2": (days(-2000), days(-900), "false"),  # end of life, not the newest
        "4.2": (days(-1200), days(-30), "false"),  # newest end of life
        "5.2": (days(-400), days(500), "true"),  # supported
    }
    return {"python": python, "django": django}


def patch_lifecycle(test):
    table = build_lifecycle()
    patcher = mock.patch(
        "probes.version_support.lifecycle", side_effect=lambda slug: table[slug]
    )
    patcher.start()
    test.addCleanup(patcher.stop)


def fake_package(python=(), django=()):
    """Just the fields `version_support` reads, with classifiers naming the versions."""
    classifiers = [f"Programming Language :: Python :: {v}" for v in python]
    classifiers += [f"Framework :: Django :: {v}" for v in django]
    return SimpleNamespace(
        pypi_classifiers=classifiers,
        pypi_requires_python="",
        pypi_info={},
        latest_version_id=None,
        latest_version=None,
    )


class SupportGradeTest(SimpleTestCase):
    def setUp(self):
        patch_lifecycle(self)

    def grade(self, slug, cycles):
        return support_grade(slug, cycles)

    def test_supported_cycle_is_full(self):
        self.assertEqual(self.grade("python", ["3.12"]), 1.0)

    def test_extended_support_is_half(self):
        self.assertEqual(self.grade("python", ["3.11"]), 0.5)

    def test_newest_end_of_life_cycle_is_half(self):
        self.assertEqual(self.grade("python", ["3.10"]), 0.5)
        self.assertEqual(self.grade("django", ["4.2"]), 0.5)

    def test_older_end_of_life_is_zero(self):
        self.assertEqual(self.grade("python", ["3.9"]), 0.0)
        self.assertEqual(self.grade("django", ["3.2"]), 0.0)

    def test_best_claimed_cycle_wins(self):
        self.assertEqual(self.grade("python", ["3.9", "3.12"]), 1.0)

    def test_support_date_decides_when_there_is_no_eol(self):
        self.assertEqual(self.grade("python", ["3.13"]), 1.0)
        self.assertEqual(self.grade("python", ["3.14"]), 0.5)

    def test_missing_support_info_counts_as_supported(self):
        self.assertEqual(self.grade("python", ["3.15"]), 1.0)

    def test_nothing_to_grade_is_none(self):
        self.assertIsNone(self.grade("python", []))
        self.assertIsNone(self.grade("python", ["2.7"]))


class VersionSupportRuleTest(SimpleTestCase):
    def setUp(self):
        patch_lifecycle(self)

    def test_python_and_django_supported_is_full(self):
        result = VersionSupportRule().check(
            package=fake_package(python=["3.12"], django=["5.2"])
        )
        self.assertEqual(result.score, 20)
        self.assertFalse(result.skipped)
        self.assertIn("Python: still supported.", result.message)
        self.assertIn("Django: still supported.", result.message)

    def test_python_only_is_graded_on_python_alone(self):
        result = VersionSupportRule().check(package=fake_package(python=["3.12"]))
        self.assertEqual(result.score, 20)
        self.assertFalse(result.skipped)

    def test_the_two_grades_are_averaged(self):
        result = VersionSupportRule().check(
            package=fake_package(python=["3.12"], django=["4.2"])
        )
        self.assertEqual(result.score, 15)
        self.assertIn("Django: near end of life.", result.message)

    def test_everything_end_of_life_scores_nothing(self):
        result = VersionSupportRule().check(
            package=fake_package(python=["3.9"], django=["3.2"])
        )
        self.assertEqual(result.score, 0)
        self.assertFalse(result.skipped)

    def test_no_version_data_is_left_out(self):
        result = VersionSupportRule().check(package=fake_package())
        self.assertTrue(result.skipped)
        self.assertEqual(result.score, 0)

    def test_unknown_cycles_are_left_out(self):
        result = VersionSupportRule().check(package=fake_package(python=["2.7"]))
        self.assertTrue(result.skipped)


class SkippedRuleTest(SimpleTestCase):
    """A skipped rule leaves the total instead of counting as zero."""

    class Full(ScoreRule):
        name: str = "full"
        description: str = "always 20"
        max_score: int = 20

        def check(self, package):
            return CheckResult(score=20, message="full")

    class Skipped(ScoreRule):
        name: str = "skipped"
        description: str = "always skipped"
        max_score: int = 20

        def check(self, package):
            return CheckResult(score=0, message="skipped", skipped=True)

    def test_skipped_rule_leaves_the_total(self):
        result = calc_package_weight(
            package=None, rules=[self.Full(), self.Skipped()], max_score=100
        )
        self.assertEqual(result["total_score"], 100)  # 20 of 20, not 20 of 40
        self.assertEqual(result["breakdown"][1]["max_score"], 0)
