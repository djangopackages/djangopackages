"""No model is involved here, so none is stubbed. The whole command is a read
of grid membership, and these cover the parts that decide what moves.
"""

import pytest
from django.core.management import call_command
from model_bakery import baker

from grid.management.commands.recategorize_from_grids import (
    GRID_CATEGORY_MAP,
    proposals,
)
from grid.models import Grid, GridPackage
from package.models import Category, Package


@pytest.fixture()
def categories(db):
    """Only apps and other are made here. The two destinations come from
    migration 0029, and making them again would leave two rows per slug,
    since Category.slug carries no unique constraint.
    """
    for slug, title, plural in [("other", "Other", "Other"), ("apps", "App", "Apps")]:
        Category.objects.get_or_create(
            slug=slug, defaults={"title": title, "title_plural": plural}
        )
    return {category.slug: category for category in Category.objects.all()}


def make_package(slug, category, grid_slugs, description="A package."):
    package = baker.make(
        Package,
        slug=slug,
        title=slug,
        category=category,
        repo_description=description,
        repo_url=f"https://github.com/example/{slug}",
    )
    for grid_slug in grid_slugs:
        grid, _ = Grid.objects.get_or_create(
            slug=grid_slug,
            defaults={"title": grid_slug.replace("-", " ").title()},
        )
        baker.make(GridPackage, grid=grid, package=package)
    return package


@pytest.mark.django_db
def test_grid_membership_decides_the_destination(categories):
    make_package("cookiecutter-django", categories["other"], ["cookiecutters"])

    moves, conflicts = proposals(["other"])

    assert conflicts == []
    assert [(p.slug, destination) for p, destination, _ in moves] == [
        ("cookiecutter-django", "starter-projects")
    ]


@pytest.mark.django_db
def test_a_package_already_in_the_right_place_is_not_a_move(categories):
    make_package("django-starter", categories["starter-projects"], ["cookiecutters"])

    moves, conflicts = proposals(["other", "starter-projects"])

    assert moves == []
    assert conflicts == []


@pytest.mark.django_db
def test_packages_outside_the_from_set_are_untouched(categories):
    make_package("django-debug-toolbar", categories["apps"], ["developer-tools"])

    moves, _ = proposals(["other"])

    assert moves == []


@pytest.mark.django_db
def test_grids_that_disagree_are_reported_not_moved(categories):
    make_package("metamon", categories["other"], ["cookiecutters", "linters"])

    moves, conflicts = proposals(["other"])

    assert moves == []
    assert len(conflicts) == 1
    package, wanted, grids = conflicts[0]
    assert package.slug == "metamon"
    assert wanted == ["developer-tools", "starter-projects"]
    assert len(grids) == 2


@pytest.mark.django_db
def test_several_grids_agreeing_is_one_move(categories):
    make_package("djlint", categories["other"], ["linters", "template-linters"])

    moves, conflicts = proposals(["other"])

    assert conflicts == []
    assert len(moves) == 1
    assert moves[0][1] == "developer-tools"


@pytest.mark.django_db
def test_unmapped_grids_are_ignored(categories):
    make_package("django-anything", categories["other"], ["forms"])

    moves, conflicts = proposals(["other"])

    assert moves == []
    assert conflicts == []


@pytest.mark.django_db
def test_to_narrows_the_map(categories):
    make_package("cookiecutter-django", categories["other"], ["cookiecutters"])
    make_package("ruff", categories["other"], ["linters"])

    moves, _ = proposals(["other"], only_to="developer-tools")

    assert [p.slug for p, _, _ in moves] == ["ruff"]


@pytest.mark.django_db
def test_read_only_by_default(categories, capsys):
    package = make_package("ruff", categories["other"], ["linters"])

    call_command("recategorize_from_grids")

    package.refresh_from_db()
    assert package.category.slug == "other"
    assert "Pass --apply" in capsys.readouterr().out


@pytest.mark.django_db
def test_apply_with_yes_refiles(categories, capsys):
    package = make_package("ruff", categories["other"], ["linters"])

    call_command("recategorize_from_grids", "--apply", "--yes")

    package.refresh_from_db()
    assert package.category.slug == "developer-tools"
    assert "1 package(s) refiled" in capsys.readouterr().out


@pytest.mark.django_db
def test_limit_caps_the_moves(categories, capsys):
    for slug in ("ruff", "black", "djlint"):
        make_package(slug, categories["other"], ["linters"])

    call_command("recategorize_from_grids", "--limit", "2", "--apply", "--yes")

    moved = Package.objects.filter(category__slug="developer-tools").count()
    assert moved == 2


@pytest.mark.django_db
def test_a_missing_from_category_is_an_error(categories):
    with pytest.raises(SystemExit):
        call_command("recategorize_from_grids", "--from", "nonsense")


@pytest.mark.django_db
def test_a_destination_nothing_maps_to_is_an_error(categories):
    with pytest.raises(SystemExit):
        call_command("recategorize_from_grids", "--to", "apps")


@pytest.mark.django_db
def test_a_destination_category_that_does_not_exist_is_an_error(categories, capsys):
    Category.objects.filter(slug="developer-tools").delete()

    with pytest.raises(SystemExit):
        call_command("recategorize_from_grids", "--to", "developer-tools")

    assert "Run migrations first" in capsys.readouterr().out


@pytest.mark.django_db
def test_nothing_to_do_says_so(categories, capsys):
    call_command("recategorize_from_grids")

    assert "Nothing to refile" in capsys.readouterr().out


def test_every_destination_in_the_map_is_a_real_category(db):
    """The map is hand-maintained. A typo in it, or a destination nobody
    migrated in, should fail here rather than at the prompt.
    """
    known = set(Category.objects.values_list("slug", flat=True))
    assert set(GRID_CATEGORY_MAP.values()) <= known
