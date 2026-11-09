"""The page behind a symbol or library row: which packages use it."""

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


def profile(slug, symbols, description=""):
    package = baker.make(
        "package.Package",
        slug=slug,
        title=slug,
        repo_url=f"https://github.com/x/{slug}",
        repo_description=description,
    )
    return baker.make(
        PackageProbe, package=package, symbols=symbols, libraries=["django"]
    )


@pytest.fixture()
def two_packages():
    profile(
        "alpha",
        [
            {"symbol": "django.urls.path", "count": 3, "library": "django"},
            {
                "symbol": "rest_framework.views.APIView",
                "count": 1,
                "library": "rest_framework",
            },
        ],
        description="Routes for everything",
    )
    profile(
        "beta",
        [{"symbol": "django.urls.path", "count": 9, "library": "django"}],
        description="Something else",
    )
    profile(
        "gamma", [{"symbol": "django.db.models.Model", "count": 2, "library": "django"}]
    )


def users_url(section, label):
    return reverse("probes:users", kwargs={"section": section, "label": label})


class TestUsersPage:
    def test_a_symbol_lists_the_packages_that_use_it(self, client, two_packages):
        response = client.get(users_url("symbols", "django.urls.path"))
        assert response.status_code == 200
        body = response.content.decode()
        assert "alpha" in body
        assert "beta" in body
        assert "gamma" not in body
        assert "Used by 2 packages, 12 times in all." in body

    def test_most_uses_come_first(self, client, two_packages):
        body = client.get(users_url("symbols", "django.urls.path")).content.decode()
        assert body.index(">beta<") < body.index(">alpha<")

    def test_a_library_sums_every_symbol_from_it(self, client, two_packages):
        body = client.get(users_url("libraries", "django")).content.decode()
        assert "Used by 3 packages, 14 times in all." in body
        body = client.get(users_url("libraries", "rest_framework")).content.decode()
        assert "Used by 1 package, 1 times in all." in body
        assert "beta" not in body

    def test_the_gone_table_shares_the_symbol_pages(self, client, two_packages):
        assert client.get(users_url("gone", "django.urls.path")).status_code == 200

    def test_a_symbol_nobody_uses_is_a_404(self, client, two_packages):
        assert client.get(users_url("symbols", "django.nothing")).status_code == 404

    def test_a_table_without_per_package_pages_is_a_404(self, client, two_packages):
        assert client.get(users_url("patterns", "queryset_filter")).status_code == 404

    def test_search_narrows_by_title_or_description(self, client, two_packages):
        url = users_url("symbols", "django.urls.path")
        body = client.get(url, {"q": "routes"}).content.decode()
        assert "alpha" in body
        assert ">beta<" not in body
        body = client.get(url, {"q": "bet"}).content.decode()
        assert ">beta<" in body
        assert ">alpha<" not in body

    def test_search_that_matches_nothing_says_so(self, client, two_packages):
        body = client.get(
            users_url("symbols", "django.urls.path"), {"q": "zzz"}
        ).content.decode()
        assert "Nothing found." in body

    def test_it_pages(self, client, settings):
        for n in range(3):
            profile(f"p{n}", [{"symbol": "django.urls.path", "count": n + 1}])
        from probes.views import ProbeUsersView

        ProbeUsersView.PER_PAGE, saved = 2, ProbeUsersView.PER_PAGE
        try:
            url = users_url("symbols", "django.urls.path")
            first = client.get(url).content.decode()
            assert "Page 1 of 2" in first
            assert ">p2<" in first and ">p0<" not in first
            second = client.get(url, {"page": 2}).content.decode()
            assert ">p0<" in second
        finally:
            ProbeUsersView.PER_PAGE = saved

    def test_htmx_gets_only_the_table(self, client, two_packages):
        response = client.get(
            users_url("symbols", "django.urls.path"),
            HTTP_HX_REQUEST="true",
            HTTP_HX_TARGET="probe-section-users",
        )
        body = response.content.decode()
        assert "<html" not in body
        assert ">alpha<" in body

    def test_it_asks_not_to_be_indexed(self, client, two_packages):
        body = client.get(users_url("symbols", "django.urls.path")).content.decode()
        assert "noindex" in body

    def test_it_links_back_to_its_table(self, client, two_packages):
        body = client.get(users_url("libraries", "django")).content.decode()
        assert reverse("probes:section", kwargs={"section": "libraries"}) in body


class TestRowLinks:
    def test_symbol_rows_link_to_their_packages(self, client, two_packages):
        body = client.get(
            reverse("probes:section", kwargs={"section": "symbols"})
        ).content.decode()
        assert users_url("symbols", "django.urls.path") in body

    def test_library_rows_link_from_the_overview(self, client, two_packages):
        body = client.get(reverse("probes:stats")).content.decode()
        assert users_url("libraries", "django") in body

    def test_every_table_links_its_rows(self):
        from probes.views import SECTIONS

        assert all(spec.users is not None for spec in SECTIONS.values())
