import pytest
from django.urls import reverse
from model_bakery import baker

from core.utils import PackageStatus
from grid.models import Grid, GridPackage
from package.models import Package, Version


def make_package(category, slug, status=None):
    package = baker.make(
        Package,
        category=category,
        slug=slug,
        title=slug,
        repo_url=f"https://github.com/example/{slug}",
    )
    if status is not None:
        version = baker.make(
            Version, package=package, number="1.0", development_status=status
        )
        Package.objects.filter(pk=package.pk).update(latest_version=version)
    return package


@pytest.fixture()
def packages(db, category):
    return {
        "stable": make_package(category, "stable-pkg", PackageStatus.STABLE),
        "beta": make_package(category, "beta-pkg", PackageStatus.BETA),
        "unknown": make_package(category, "unknown-pkg", PackageStatus.UNKNOWN),
        "no_release": make_package(category, "no-release-pkg"),
    }


def titles(response):
    return {package.slug for package in response.context["packages"]}


def test_no_status_shows_everything(client, packages):
    response = client.get(reverse("packages"))

    assert titles(response) == set(p.slug for p in packages.values())
    assert response.context["current_status"] == "all"


def test_status_narrows_to_that_release_status(client, packages):
    response = client.get(reverse("packages"), {"status": PackageStatus.STABLE})

    assert titles(response) == {"stable-pkg"}
    assert response.context["current_status"] == str(PackageStatus.STABLE.value)


def test_unknown_includes_packages_with_no_release(client, packages):
    response = client.get(reverse("packages"), {"status": PackageStatus.UNKNOWN})

    assert titles(response) == {"unknown-pkg", "no-release-pkg"}


def test_invalid_status_falls_back_to_all(client, packages):
    response = client.get(reverse("packages"), {"status": "99"})

    assert len(titles(response)) == 4
    assert response.context["current_status"] == "all"


def test_status_combines_with_search(client, packages):
    response = client.get(
        reverse("packages"), {"status": PackageStatus.BETA, "q": "stable"}
    )

    assert titles(response) == set()


def test_status_filter_on_grid_package_list(client, packages):
    grid = baker.make(Grid, slug="g", title="G", is_approved=True)
    for package in packages.values():
        GridPackage.objects.create(grid=grid, package=package)

    response = client.get(
        reverse("grid_packages", kwargs={"slug": "g"}),
        {"status": PackageStatus.BETA},
    )

    assert titles(response) == {"beta-pkg"}


def test_status_filter_on_category_list(client, packages, category):
    response = client.get(
        reverse("category", kwargs={"slug": category.slug}),
        {"status": PackageStatus.STABLE},
    )

    assert titles(response) == {"stable-pkg"}


def test_status_is_carried_in_the_htmx_state(client, packages):
    response = client.get(reverse("packages"), {"status": PackageStatus.STABLE})

    body = response.content.decode()
    assert (
        f'<input type="hidden" name="status" value="{PackageStatus.STABLE.value}">'
        in body
    )
    assert f'&status={PackageStatus.STABLE.value}"' in body
