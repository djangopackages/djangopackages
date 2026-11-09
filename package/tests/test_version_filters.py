"""Django and Python version filters on the package lists, from probe data."""

import pytest
from django.core.cache import cache
from django.urls import reverse
from model_bakery import baker

from probes.models import PackageProbe

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def empty_cache():
    cache.clear()
    yield
    cache.clear()


@pytest.fixture()
def category():
    return baker.make("package.Category", slug="apps", title="Apps")


def package(slug, category, django=None, python=None):
    pkg = baker.make(
        "package.Package",
        slug=slug,
        title=slug,
        category=category,
        repo_url=f"https://github.com/x/{slug}",
    )
    if django is not None or python is not None:
        baker.make(
            PackageProbe,
            package=pkg,
            django_versions=django or [],
            python_versions=python or [],
        )
    return pkg


@pytest.fixture()
def packages(category):
    package("old", category, django=["4.2"], python=["3.8", "3.9"])
    package("new", category, django=["5.1", "5.2"], python=["3.12", "3.13"])
    package("both", category, django=["4.2", "5.2"], python=["3.9", "3.12"])
    package("unprobed", category)


def titles(response):
    body = response.content.decode()
    return {name for name in ("old", "new", "both", "unprobed") if f">{name}<" in body}


class TestVersionFilters:
    def test_no_filter_shows_everything(self, client, packages):
        assert titles(client.get(reverse("packages"))) == {
            "old",
            "new",
            "both",
            "unprobed",
        }

    def test_a_django_cycle_narrows_to_packages_that_claim_it(self, client, packages):
        response = client.get(reverse("packages"), {"django_version": "5.2"})
        assert titles(response) == {"new", "both"}

    def test_a_python_cycle_does_too(self, client, packages):
        response = client.get(reverse("packages"), {"python_version": "3.9"})
        assert titles(response) == {"old", "both"}

    def test_both_together_intersect(self, client, packages):
        response = client.get(
            reverse("packages"), {"django_version": "4.2", "python_version": "3.12"}
        )
        assert titles(response) == {"both"}

    def test_unprobed_packages_drop_out_once_a_version_is_chosen(
        self, client, packages
    ):
        response = client.get(reverse("packages"), {"django_version": "4.2"})
        assert "unprobed" not in titles(response)

    def test_a_version_nobody_claims_reads_as_all(self, client, packages):
        response = client.get(reverse("packages"), {"django_version": "1.4"})
        assert titles(response) == {"old", "new", "both", "unprobed"}
        assert response.context["current_django_version"] == "all"

    def test_only_claimed_versions_are_offered_newest_first(self, client, packages):
        response = client.get(reverse("packages"))
        offered = [row.label for row in response.context["django_version_choices"]]
        assert offered == ["5.2", "5.1", "4.2"]
        offered = [row.label for row in response.context["python_version_choices"]]
        assert offered == ["3.13", "3.12", "3.9", "3.8"]

    def test_the_choice_survives_in_the_hidden_state_and_links(self, client, packages):
        body = client.get(
            reverse("packages"), {"django_version": "5.2"}
        ).content.decode()
        assert '<input type="hidden" name="django_version" value="5.2">' in body
        assert "&django_version=5.2&python_version=all" in body

    def test_no_selects_when_nothing_is_probed(self, client, category):
        package("plain", category)
        body = client.get(reverse("packages")).content.decode()
        assert "package-django-version-filter" not in body

    def test_it_works_with_the_search_and_status_filters(self, client, packages):
        response = client.get(reverse("packages"), {"django_version": "5.2", "q": "bo"})
        assert titles(response) == {"both"}

    def test_the_category_list_filters_too(self, client, packages, category):
        response = client.get(
            reverse("category", kwargs={"slug": category.slug}),
            {"python_version": "3.13"},
        )
        assert titles(response) == {"new"}

    def test_the_grid_list_filters_too(self, client, packages):
        from package.models import Package

        grid = baker.make("grid.Grid", slug="g", title="g")
        for pkg in Package.objects.all():
            baker.make("grid.GridPackage", grid=grid, package=pkg)
        response = client.get(
            reverse("grid_packages", kwargs={"slug": grid.slug}),
            {"django_version": "4.2"},
        )
        assert titles(response) == {"old", "both"}

    def test_htmx_swaps_carry_the_filter(self, client, packages):
        response = client.get(
            reverse("packages"),
            {"django_version": "5.2"},
            HTTP_HX_REQUEST="true",
        )
        assert titles(response) == {"new", "both"}
        assert "<html" not in response.content.decode()
