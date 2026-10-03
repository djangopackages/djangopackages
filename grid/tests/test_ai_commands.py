"""The confidence filtering is ours, so it gets tested; Jev is stubbed out.

Real calls were used to tune the questions, but a test suite that hits the API
would be slow, costly, and non-deterministic.
"""

from unittest.mock import Mock, patch

import pytest
from django.core.management import call_command
from model_bakery import baker

from grid.ai import GridVerdict, PackageVerdict, Quality
from grid.models import Grid, GridPackage
from package.models import Category, Package


@pytest.fixture()
def category(db):
    return baker.make(Category, slug="apps", title="App", title_plural="Apps")


@pytest.fixture()
def grid(db, category):
    g = baker.make(Grid, slug="bundlers", title="Bundlers", is_approved=True)
    package = baker.make(
        Package,
        slug="django-vite",
        title="django-vite",
        category=category,
        repo_url="https://github.com/example/django-vite",
    )
    baker.make(GridPackage, grid=g, package=package)
    return g


def fake_result(output, confidence):
    result = Mock()
    result.output = output
    result.response.provider_details = {"confidence": confidence}
    return result


def stub_agent(result):
    agent = Mock()
    agent.run_sync.return_value = result
    return agent


@pytest.mark.django_db
def test_confident_bad_rubric_is_flagged(grid, capsys):
    verdict = GridVerdict(
        topic_coherence=Quality.STRONG,
        title_and_description=Quality.UNUSABLE,
        useful_as_comparison=Quality.DECENT,
    )
    confidence = {
        "topic_coherence": 0.95,
        "title_and_description": 0.99,
        "useful_as_comparison": 0.90,
    }

    with patch(
        "grid.management.commands.evaluate_grids.build_agent",
        return_value=stub_agent(fake_result(verdict, confidence)),
    ):
        call_command("evaluate_grids", "--limit", "0")

    out = capsys.readouterr().out
    assert "needs work: 1" in out
    assert "title_and_description" in out


@pytest.mark.django_db
def test_unsure_bad_rubric_is_not_flagged(grid, capsys):
    """A low-confidence UNUSABLE must not read as a recommendation."""
    verdict = GridVerdict(
        topic_coherence=Quality.STRONG,
        title_and_description=Quality.UNUSABLE,
        useful_as_comparison=Quality.DECENT,
    )
    confidence = {
        "topic_coherence": 0.95,
        "title_and_description": 0.20,
        "useful_as_comparison": 0.90,
    }

    with patch(
        "grid.management.commands.evaluate_grids.build_agent",
        return_value=stub_agent(fake_result(verdict, confidence)),
    ):
        call_command("evaluate_grids", "--limit", "0")

    out = capsys.readouterr().out
    assert "needs work: 0" in out


@pytest.mark.django_db
def test_missing_confidence_counts_as_unsure(grid, capsys):
    verdict = GridVerdict(
        topic_coherence=Quality.UNUSABLE,
        title_and_description=Quality.UNUSABLE,
        useful_as_comparison=Quality.UNUSABLE,
    )

    with patch(
        "grid.management.commands.evaluate_grids.build_agent",
        return_value=stub_agent(fake_result(verdict, {})),
    ):
        call_command("evaluate_grids", "--limit", "0")

    out = capsys.readouterr().out
    assert "needs work: 0" in out
    assert "unsure" in out


@pytest.mark.django_db
def test_confident_category_disagreement_is_reported(grid, capsys):
    verdict = PackageVerdict(belongs_in_grid=True, installation_type="frameworks")
    confidence = {"belongs_in_grid": 0.95, "installation_type": 0.97}

    with patch(
        "grid.management.commands.evaluate_grid_packages.build_agent",
        return_value=stub_agent(fake_result(verdict, confidence)),
    ):
        call_command("evaluate_grid_packages", "--limit", "0")

    out = capsys.readouterr().out
    assert "category disagreement: 1" in out
    assert "frameworks" in out


@pytest.mark.django_db
def test_unsure_category_disagreement_is_not_reported(grid, capsys):
    verdict = PackageVerdict(belongs_in_grid=True, installation_type="frameworks")
    confidence = {"belongs_in_grid": 0.95, "installation_type": 0.40}

    with patch(
        "grid.management.commands.evaluate_grid_packages.build_agent",
        return_value=stub_agent(fake_result(verdict, confidence)),
    ):
        call_command("evaluate_grid_packages", "--limit", "0")

    out = capsys.readouterr().out
    assert "category disagreement: 0" in out


@pytest.mark.django_db
def test_confident_removal_is_reported(grid, capsys):
    verdict = PackageVerdict(belongs_in_grid=False, installation_type="apps")
    confidence = {"belongs_in_grid": 0.93, "installation_type": 0.99}

    with patch(
        "grid.management.commands.evaluate_grid_packages.build_agent",
        return_value=stub_agent(fake_result(verdict, confidence)),
    ):
        call_command("evaluate_grid_packages", "--limit", "0")

    out = capsys.readouterr().out
    assert "would remove from grid: 1" in out


@pytest.mark.django_db
def test_nothing_is_written_to_the_database(grid, capsys):
    verdict = PackageVerdict(belongs_in_grid=False, installation_type="frameworks")
    confidence = {"belongs_in_grid": 0.99, "installation_type": 0.99}

    before = list(
        GridPackage.objects.values_list(
            "grid__slug", "package__slug", "package__category__slug"
        )
    )

    with patch(
        "grid.management.commands.evaluate_grid_packages.build_agent",
        return_value=stub_agent(fake_result(verdict, confidence)),
    ):
        call_command("evaluate_grid_packages", "--limit", "0")

    after = list(
        GridPackage.objects.values_list(
            "grid__slug", "package__slug", "package__category__slug"
        )
    )
    assert before == after
