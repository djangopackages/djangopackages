from datetime import timedelta

import pytest
from click.testing import CliRunner
from django.utils import timezone
from model_bakery import baker

from grid.models import Grid, GridPackage
from package.management.commands.compare_scores import command
from package.models import Category, Package


@pytest.fixture
def grid_with_packages(db):
    category = Category.objects.create(title="Apps", slug="apps")
    grid = Grid.objects.create(title="Ecommerce", slug="ecommerce", is_approved=True)
    now = timezone.now()
    fresh = baker.make(
        Package,
        title="fresh",
        slug="fresh",
        category=category,
        repo_url="https://github.com/t/fresh",
        repo_description="Fresh and described",
        documentation_url="https://fresh.readthedocs.io/",
        repo_watchers=5_000,
        repo_forks=0,
        pypi_downloads=0,
        last_commit_date=now - timedelta(days=3),
        score=5_000,
    )
    stale = baker.make(
        Package,
        title="stale",
        slug="stale",
        category=category,
        repo_url="https://github.com/t/stale",
        repo_description="Stale and described",
        repo_watchers=20_000,
        repo_forks=0,
        pypi_downloads=0,
        last_commit_date=now - timedelta(days=365 * 5),
        score=4_000,
    )
    for package in (fresh, stale):
        GridPackage.objects.create(grid=grid, package=package)
    return grid


def test_compare_scores_runs_and_writes_nothing(grid_with_packages, settings, tmp_path):
    settings.PACKAGE_SCORE_MIN = 50
    before = dict(Package.objects.values_list("slug", "score"))
    csv_path = tmp_path / "scores.csv"

    result = CliRunner().invoke(
        command, ["--grid", "ecommerce", "--grid", "missing", "--csv", str(csv_path)]
    )

    assert result.exit_code == 0, result.output
    assert "2 active packages, 1 approved grids" in result.output
    assert "Effect on the grids" in result.output
    # Under the stored scores both show and stale is on top. Under the
    # rules fresh is 57 (not deprecated, description, documentation,
    # usage floor, watchers: 81 of 140) and stale fades to single digits,
    # so at a cutoff of 50 stale drops and the top changes.
    assert "Points by rule" in result.output
    assert "grids whose top package changes" in result.output
    assert "stored only" in result.output
    assert "No approved grid with slug 'missing'" in result.output
    assert dict(Package.objects.values_list("slug", "score")) == before
    assert csv_path.read_text().count("\n") == 3


def test_new_min_is_an_option(grid_with_packages):
    result = CliRunner().invoke(command, ["--new-min", "1"])
    assert result.exit_code == 0, result.output
    assert "computed cutoff 1" in result.output
