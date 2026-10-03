"""The confidence filtering is ours, so it gets tested; Jev is stubbed out.

Real calls were used to tune the questions, but a test suite that hits the API
would be slow, costly, and non-deterministic.
"""

from unittest.mock import Mock, patch

import pytest
from django.core.management import call_command
from model_bakery import baker

from grid.ai import ElementVerdict, GridVerdict, PackageVerdict, Quality
from grid.models import Element, Feature, Grid, GridPackage
from package.models import Category, Package


@pytest.fixture()
def category(db):
    return baker.make(Category, slug="apps", title="App", title_plural="Apps")


@pytest.fixture()
def grid(db, category):
    """Two packages, since a grid with fewer is removed on the count alone."""
    g = baker.make(Grid, slug="bundlers", title="Bundlers", is_approved=True)
    for slug in ("django-vite", "django-webpack-loader"):
        package = baker.make(
            Package,
            slug=slug,
            title=slug,
            category=category,
            repo_url=f"https://github.com/example/{slug}",
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
        topic_is_worth_a_grid=True,
    )
    confidence = {
        "topic_coherence": 0.95,
        "title_and_description": 0.99,
        "useful_as_comparison": 0.90,
        "topic_is_worth_a_grid": 0.95,
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
        topic_is_worth_a_grid=True,
    )
    confidence = {
        "topic_coherence": 0.95,
        "title_and_description": 0.20,
        "useful_as_comparison": 0.90,
        "topic_is_worth_a_grid": 0.95,
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
        topic_is_worth_a_grid=True,
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
def test_confident_removal_of_a_grid_is_reported(grid, capsys):
    verdict = GridVerdict(
        topic_coherence=Quality.UNUSABLE,
        title_and_description=Quality.UNUSABLE,
        useful_as_comparison=Quality.UNUSABLE,
        topic_is_worth_a_grid=False,
    )
    confidence = {
        "topic_coherence": 0.95,
        "title_and_description": 0.95,
        "useful_as_comparison": 0.95,
        "topic_is_worth_a_grid": 0.97,
    }

    with patch(
        "grid.management.commands.evaluate_grids.build_agent",
        return_value=stub_agent(fake_result(verdict, confidence)),
    ):
        call_command("evaluate_grids", "--limit", "0")

    out = capsys.readouterr().out
    assert "would remove: 1" in out
    assert "no field of packages for this topic" in out


@pytest.mark.django_db
def test_unsure_removal_of_a_grid_is_not_reported(grid, capsys):
    """A hesitant delete must not read as a recommendation."""
    verdict = GridVerdict(
        topic_coherence=Quality.DECENT,
        title_and_description=Quality.DECENT,
        useful_as_comparison=Quality.DECENT,
        topic_is_worth_a_grid=False,
    )
    confidence = {
        "topic_coherence": 0.95,
        "title_and_description": 0.95,
        "useful_as_comparison": 0.95,
        "topic_is_worth_a_grid": 0.40,
    }

    with patch(
        "grid.management.commands.evaluate_grids.build_agent",
        return_value=stub_agent(fake_result(verdict, confidence)),
    ):
        call_command("evaluate_grids", "--limit", "0")

    out = capsys.readouterr().out
    assert "would remove: 0" in out


@pytest.mark.django_db
def test_no_grid_is_deleted_by_the_review(grid, capsys):
    verdict = GridVerdict(
        topic_coherence=Quality.UNUSABLE,
        title_and_description=Quality.UNUSABLE,
        useful_as_comparison=Quality.UNUSABLE,
        topic_is_worth_a_grid=False,
    )
    confidence = {
        "topic_coherence": 0.99,
        "title_and_description": 0.99,
        "useful_as_comparison": 0.99,
        "topic_is_worth_a_grid": 0.99,
    }

    with patch(
        "grid.management.commands.evaluate_grids.build_agent",
        return_value=stub_agent(fake_result(verdict, confidence)),
    ):
        call_command("evaluate_grids", "--limit", "0")

    assert Grid.objects.filter(slug="bundlers").exists()


@pytest.mark.django_db
def test_confident_category_disagreement_is_reported(grid, capsys):
    verdict = PackageVerdict(belongs_in_grid=True, installation_type="frameworks")
    confidence = {"belongs_in_grid": 0.95, "installation_type": 0.97}

    with patch(
        "grid.management.commands.evaluate_grid_packages.build_agent",
        return_value=stub_agent(fake_result(verdict, confidence)),
    ):
        call_command("evaluate_grid_packages", "--limit", "1")

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
        call_command("evaluate_grid_packages", "--limit", "1")

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
        call_command("evaluate_grid_packages", "--limit", "1")

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
        call_command("evaluate_grid_packages", "--limit", "1")

    after = list(
        GridPackage.objects.values_list(
            "grid__slug", "package__slug", "package__category__slug"
        )
    )
    assert before == after


@pytest.fixture()
def element(db, grid):
    feature = baker.make(Feature, grid=grid, title="Async support", description="")
    return baker.make(
        Element,
        grid_package=GridPackage.objects.filter(grid=grid).first(),
        feature=feature,
        text="Only for Postgres",
    )


@pytest.mark.django_db
def test_legend_cells_never_reach_jev(element, capsys):
    element.text = "yes"
    element.save()

    agent = stub_agent(fake_result(None, {}))
    with patch(
        "grid.management.commands.evaluate_grid_elements.build_agent",
        return_value=agent,
    ):
        call_command("evaluate_grid_elements", "--limit", "0")

    agent.run_sync.assert_not_called()
    out = capsys.readouterr().out
    assert "supported: 1" in out
    assert "legend" in out


@pytest.mark.django_db
def test_all_cells_sends_legend_cells_to_jev(element, capsys):
    element.text = "yes"
    element.save()

    verdict = ElementVerdict(support="supported", is_placeholder=False)
    agent = stub_agent(fake_result(verdict, {"support": 0.99, "is_placeholder": 0.99}))
    with patch(
        "grid.management.commands.evaluate_grid_elements.build_agent",
        return_value=agent,
    ):
        call_command("evaluate_grid_elements", "--limit", "0", "--all-cells")

    agent.run_sync.assert_called_once()


@pytest.mark.django_db
def test_confident_partial_is_counted(element, capsys):
    verdict = ElementVerdict(support="partial", is_placeholder=False)
    confidence = {"support": 0.95, "is_placeholder": 0.97}

    with patch(
        "grid.management.commands.evaluate_grid_elements.build_agent",
        return_value=stub_agent(fake_result(verdict, confidence)),
    ):
        call_command("evaluate_grid_elements", "--limit", "0")

    out = capsys.readouterr().out
    assert "partial: 1" in out
    assert "says nothing: 0" in out


@pytest.mark.django_db
def test_confident_placeholder_is_flagged(element, capsys):
    element.text = "TODO"
    element.save()

    verdict = ElementVerdict(support="unknown", is_placeholder=True)
    confidence = {"support": 0.96, "is_placeholder": 0.98}

    with patch(
        "grid.management.commands.evaluate_grid_elements.build_agent",
        return_value=stub_agent(fake_result(verdict, confidence)),
    ):
        call_command("evaluate_grid_elements", "--limit", "0")

    out = capsys.readouterr().out
    assert "says nothing: 1" in out
    assert "Cells that answer nothing" in out


@pytest.mark.django_db
def test_unsure_cell_is_not_counted(element, capsys):
    verdict = ElementVerdict(support="partial", is_placeholder=True)
    confidence = {"support": 0.30, "is_placeholder": 0.30}

    with patch(
        "grid.management.commands.evaluate_grid_elements.build_agent",
        return_value=stub_agent(fake_result(verdict, confidence)),
    ):
        call_command("evaluate_grid_elements", "--limit", "0")

    out = capsys.readouterr().out
    assert "unsure: 1" in out
    assert "says nothing: 0" in out


@pytest.mark.django_db
def test_cell_text_is_left_alone(element, capsys):
    verdict = ElementVerdict(support="not_supported", is_placeholder=True)
    confidence = {"support": 0.99, "is_placeholder": 0.99}

    with patch(
        "grid.management.commands.evaluate_grid_elements.build_agent",
        return_value=stub_agent(fake_result(verdict, confidence)),
    ):
        call_command("evaluate_grid_elements", "--limit", "0")

    element.refresh_from_db()
    assert element.text == "Only for Postgres"


@pytest.mark.django_db
def test_a_one_package_grid_is_removed_without_asking(db, category, capsys):
    """Emptiness is a count, not a judgement call."""
    lonely = baker.make(Grid, slug="webdesign", title="Webdesign", is_approved=True)
    package = baker.make(Package, slug="django-webdesign", category=category)
    baker.make(GridPackage, grid=lonely, package=package)

    verdict = GridVerdict(
        topic_coherence=Quality.STRONG,
        title_and_description=Quality.STRONG,
        useful_as_comparison=Quality.STRONG,
        topic_is_worth_a_grid=True,
    )
    confidence = {
        "topic_coherence": 0.99,
        "title_and_description": 0.99,
        "useful_as_comparison": 0.99,
        "topic_is_worth_a_grid": 0.99,
    }

    with patch(
        "grid.management.commands.evaluate_grids.build_agent",
        return_value=stub_agent(fake_result(verdict, confidence)),
    ):
        call_command("evaluate_grids", "--slug", "webdesign")

    out = capsys.readouterr().out
    assert "would remove: 1" in out
    assert "only 1 package(s)" in out


@pytest.fixture()
def other_category(db):
    return baker.make(Category, slug="other", title="Other", title_plural="Other")


@pytest.fixture()
def package_in_other(db, other_category, grid):
    """One package filed under Other, listed on two grids."""
    package = baker.make(
        Package,
        slug="django-extensions",
        title="django-extensions",
        category=other_category,
        repo_url="https://github.com/example/django-extensions",
    )
    second = baker.make(Grid, slug="shells", title="Shells", is_approved=True)
    baker.make(GridPackage, grid=grid, package=package)
    baker.make(GridPackage, grid=second, package=package)
    return package


@pytest.mark.django_db
def test_category_sweep_skips_other_categories(package_in_other, capsys):
    verdict = PackageVerdict(belongs_in_grid=True, installation_type="apps")
    confidence = {"belongs_in_grid": 0.95, "installation_type": 0.97}

    with patch(
        "grid.management.commands.evaluate_grid_packages.build_agent",
        return_value=stub_agent(fake_result(verdict, confidence)),
    ):
        call_command("evaluate_grid_packages", "--limit", "0", "--category", "other")

    out = capsys.readouterr().out
    assert "django-extensions" in out
    assert "django-vite" not in out


@pytest.mark.django_db
def test_category_sweep_asks_once_per_package(package_in_other, capsys):
    """The package sits on two grids, but its installation type is one answer."""
    verdict = PackageVerdict(belongs_in_grid=True, installation_type="apps")
    agent = stub_agent(
        fake_result(verdict, {"belongs_in_grid": 0.95, "installation_type": 0.97})
    )

    with patch(
        "grid.management.commands.evaluate_grid_packages.build_agent",
        return_value=agent,
    ):
        call_command("evaluate_grid_packages", "--limit", "0", "--category", "other")

    assert agent.run_sync.call_count == 1


@pytest.mark.django_db
def test_category_sweep_groups_moves_by_destination(package_in_other, capsys):
    verdict = PackageVerdict(belongs_in_grid=True, installation_type="apps")
    confidence = {"belongs_in_grid": 0.95, "installation_type": 0.97}

    with patch(
        "grid.management.commands.evaluate_grid_packages.build_agent",
        return_value=stub_agent(fake_result(verdict, confidence)),
    ):
        call_command("evaluate_grid_packages", "--limit", "0", "--category", "other")

    out = capsys.readouterr().out
    assert "Moves to make, by destination" in out
    assert "-> apps (1)" in out
    assert "django-extensions (from other)" in out


@pytest.mark.django_db
def test_unknown_category_is_rejected(package_in_other):
    with pytest.raises(SystemExit):
        call_command("evaluate_grid_packages", "--category", "nope")


@pytest.mark.django_db
def test_category_sweep_writes_nothing(package_in_other):
    verdict = PackageVerdict(belongs_in_grid=False, installation_type="frameworks")
    confidence = {"belongs_in_grid": 0.99, "installation_type": 0.99}

    with patch(
        "grid.management.commands.evaluate_grid_packages.build_agent",
        return_value=stub_agent(fake_result(verdict, confidence)),
    ):
        call_command("evaluate_grid_packages", "--limit", "0", "--category", "other")

    package_in_other.refresh_from_db()
    assert package_in_other.category.slug == "other"
