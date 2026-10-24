"""The new 0 to 100 package score (#1563). Legacy tests stay in test_scores.py."""

from datetime import timedelta

import pytest
from django.utils import timezone
from model_bakery import baker

from package.models import Category, Package, Version
from package.scoring import (
    ScoreInputs,
    ScoreWeights,
    calculate_score,
    explain_score,
)

NOW = timezone.now()
WEIGHTS = ScoreWeights()


def ago(days: int):
    return NOW - timedelta(days=days)


def score(**kwargs) -> int:
    return calculate_score(ScoreInputs(**kwargs), WEIGHTS, now=NOW)


def test_fresh_package_at_the_caps_scores_100():
    assert (
        score(
            repo_watchers=WEIGHTS.stars_cap,
            pypi_downloads=WEIGHTS.downloads_cap,
            last_commit_date=ago(1),
            last_release_date=ago(1),
        )
        == 100
    )


def test_nothing_known_scores_zero():
    assert score() == 0


def test_deprecated_and_archived_are_a_hard_zero():
    popular = dict(
        repo_watchers=100_000,
        pypi_downloads=10_000_000,
        last_commit_date=ago(1),
        last_release_date=ago(1),
    )
    assert score(**popular) == 100
    assert score(**popular, is_deprecated=True) == 0
    assert score(**popular, is_archived=True) == 0
    assert (
        explain_score(ScoreInputs(**popular, is_archived=True), now=NOW).zeroed_by
        == "archived"
    )


def test_stars_are_log_scaled():
    """50,000 stars is worth more than 500, but nowhere near 100 times more."""
    small = score(repo_watchers=500, last_commit_date=ago(1), last_release_date=ago(1))
    big = score(repo_watchers=50_000, last_commit_date=ago(1), last_release_date=ago(1))
    assert small < big
    assert big < 2 * small


def test_stars_above_the_cap_add_nothing():
    at_cap = score(repo_watchers=50_000, last_commit_date=ago(1))
    assert score(repo_watchers=500_000, last_commit_date=ago(1)) == at_cap


def test_abandoned_package_decays_to_zero_whatever_its_stars():
    """The legacy formula let a big abandoned package coast for years."""
    fresh = score(
        repo_watchers=50_000, last_commit_date=ago(30), last_release_date=ago(30)
    )
    stale = score(
        repo_watchers=50_000,
        last_commit_date=ago(365 * 2),
        last_release_date=ago(365 * 2),
    )
    dead = score(
        repo_watchers=50_000,
        last_commit_date=ago(365 * 4),
        last_release_date=ago(365 * 4),
    )
    assert fresh == 100
    assert 0 < stale < fresh
    assert dead == 0


def test_freshness_is_flat_for_a_year_then_falls_linearly():
    assert score(repo_watchers=50_000, last_commit_date=ago(1)) == score(
        repo_watchers=50_000, last_commit_date=ago(364)
    )
    halfway = (WEIGHTS.fresh_days + WEIGHTS.stale_days) // 2
    assert score(repo_watchers=50_000, last_commit_date=ago(halfway)) == 50


def test_release_outweighs_commits():
    """#1144: Saleor commits daily but has not shipped to PyPI since 2020."""
    saleor = score(
        repo_watchers=23_000, last_commit_date=ago(2), last_release_date=ago(365 * 6)
    )
    oscar = score(
        repo_watchers=7_000, last_commit_date=ago(60), last_release_date=ago(60)
    )
    assert oscar > saleor
    # Still shipping but quiet on GitHub beats the reverse.
    ships = score(
        repo_watchers=1_000, last_commit_date=ago(365 * 5), last_release_date=ago(10)
    )
    commits = score(
        repo_watchers=1_000, last_commit_date=ago(10), last_release_date=ago(365 * 5)
    )
    assert ships > commits


def test_missing_signals_are_left_out_not_read_as_zero():
    """A package that is not on PyPI is judged on its commits alone."""
    on_pypi = score(
        repo_watchers=1_000, last_commit_date=ago(10), last_release_date=ago(10)
    )
    off_pypi = score(repo_watchers=1_000, last_commit_date=ago(10))
    assert off_pypi == on_pypi
    # Likewise an unknown download count does not drag popularity down.
    with_downloads = explain_score(
        ScoreInputs(repo_watchers=1_000, pypi_downloads=1, last_commit_date=ago(10)),
        now=NOW,
    )
    without = explain_score(
        ScoreInputs(repo_watchers=1_000, last_commit_date=ago(10)), now=NOW
    )
    assert without.downloads_part is None
    assert with_downloads.popularity < without.popularity


def test_downloads_count_when_known():
    quiet = score(repo_watchers=1_000, pypi_downloads=1_000, last_commit_date=ago(10))
    busy = score(
        repo_watchers=1_000, pypi_downloads=1_000_000, last_commit_date=ago(10)
    )
    assert quiet < busy


def test_score_is_bounded_and_integer():
    for stars in (0, 1, 10, 10**6):
        for downloads in (0, 1, 10**9):
            value = score(
                repo_watchers=stars, pypi_downloads=downloads, last_commit_date=ago(1)
            )
            assert isinstance(value, int)
            assert 0 <= value <= 100


def test_weights_are_tunable():
    strict = ScoreWeights(fresh_days=30, stale_days=60)
    inputs = ScoreInputs(repo_watchers=50_000, last_commit_date=ago(90))
    assert calculate_score(inputs, now=NOW) == 100
    assert calculate_score(inputs, strict, now=NOW) == 0


@pytest.mark.django_db
def test_inputs_from_package_reads_the_latest_version():
    category = Category.objects.create(title="Apps", slug="apps")
    package = baker.make(
        Package,
        category=category,
        repo_url="https://github.com/test/scoring-inputs",
        repo_watchers=12,
        pypi_downloads=34,
        last_commit_date=ago(5),
        date_repo_archived=ago(1),
    )
    version = Version.objects.create(package=package, number="1.0", upload_time=ago(7))
    package.latest_version = version
    package.save()

    inputs = ScoreInputs.from_package(package)

    assert inputs == ScoreInputs(
        repo_watchers=12,
        pypi_downloads=34,
        last_commit_date=package.last_commit_date,
        last_release_date=version.upload_time,
        is_deprecated=False,
        is_archived=True,
    )
    assert calculate_score(inputs) == 0
