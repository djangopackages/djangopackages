"""The unlisted stats page."""

import sys
import types

import pytest
from django.core.cache import cache
from django.urls import reverse
from model_bakery import baker

from probes.models import PackageProbe

pytestmark = pytest.mark.django_db


@pytest.fixture()
def profile():
    package = baker.make(
        "package.Package",
        slug="a",
        title="a",
        repo_url="https://github.com/x/a",
    )
    return baker.make(
        PackageProbe,
        package=package,
        python_versions=["3.11", "3.12"],
        python_source=PackageProbe.Source.CLASSIFIERS,
        django_versions=["5.1", "5.2"],
        django_source=PackageProbe.Source.CLASSIFIERS,
        dependencies=[
            {"name": "django", "specifier": ">=5.1", "extra": "", "marker": ""}
        ],
        symbols=[
            {"symbol": "django.urls.path", "count": 3, "library": "django"},
            {
                "symbol": "django.utils.translation.ugettext_lazy",
                "count": 2,
                "library": "django",
            },
            {"symbol": "django.conf.settings.DEBUG", "count": 1, "library": "django"},
        ],
        patterns=[{"pattern": "probe:queryset_filter", "count": 5}],
        libraries=["django"],
        files_scanned=7,
    )


@pytest.fixture(autouse=True)
def empty_cache():
    """The roll-ups are cached, and one test's would answer the next.

    Cleared rather than swapped for a dummy backend, since other apps
    hold named caches that replacing CACHES would take away.
    """
    cache.clear()
    yield
    cache.clear()


@pytest.fixture()
def catalogued(profile):
    """What `build_probe_catalog --check` would have written.

    The gone table reads the catalogue rather than importing each
    dotted path, so a profile on its own is not enough to put a symbol
    in it; the catalogue has to have been checked.
    """
    import django

    from probes.models import ProbeSymbol

    baker.make(
        ProbeSymbol,
        kind=ProbeSymbol.Kind.SYMBOL,
        library="django",
        name="django.utils.translation.ugettext_lazy",
        missing=True,
        checked_against=django.get_version(),
    )
    cache.clear()
    return profile


class TestProbeStatsPage:
    def test_it_needs_no_login(self, client, profile):
        """Unlisted, not private: a password would only stop us looking."""
        response = client.get(reverse("probes:stats"))

        assert response.status_code == 200

    def test_it_asks_not_to_be_indexed(self, client, profile):
        response = client.get(reverse("probes:stats"))

        assert b"noindex" in response.content

    def test_it_shows_the_version_shares(self, client, profile):
        response = client.get(reverse("probes:stats"))
        content = response.content.decode()

        assert "5.2" in content
        assert "3.12" in content

    def test_it_shows_patterns_and_settings(self, client, profile):
        response = client.get(reverse("probes:stats"))
        content = response.content.decode()

        assert "queryset_filter" in content
        assert "DEBUG" in content

    def test_it_names_the_apis_django_no_longer_has(self, client, profile):
        response = client.get(reverse("probes:stats"))

        assert b"ugettext_lazy" in response.content

    def test_each_table_pages_on_its_own_parameter(self, client, profile):
        """Paging the symbols must not reset the settings table."""
        response = client.get(reverse("probes:stats"), {"symbols": 2, "settings": 1})

        assert response.status_code == 200
        sections = {section["param"] for section in response.context["sections"]}
        assert {"symbols", "settings", "patterns", "deps", "libraries"} <= sections

    def test_an_out_of_range_page_does_not_break_it(self, client, profile):
        response = client.get(reverse("probes:stats"), {"symbols": 9999})

        assert response.status_code == 200

    def test_an_empty_database_says_so_rather_than_erroring(self, client):
        response = client.get(reverse("probes:stats"))

        assert response.status_code == 200
        assert b"No profiles yet" in response.content


class TestColumnsMatchTheirFields:
    """A table's third column must be the field it names."""

    def test_dependencies_report_how_many_require_them(self, client):
        package = baker.make(
            "package.Package", slug="d", title="d", repo_url="https://github.com/x/d"
        )
        baker.make(
            PackageProbe,
            package=package,
            dependencies=[
                {"name": "django", "specifier": "", "extra": "", "marker": ""},
                {"name": "boto3", "specifier": "", "extra": "s3", "marker": ""},
            ],
        )

        response = client.get(reverse("probes:stats"))
        section = next(s for s in response.context["sections"] if s["param"] == "deps")
        rows = {row["label"]: row["values"] for row in section["rows"]}

        # [depended on by, required by]: boto3 is behind an extra.
        assert rows["django"] == [1, 1]
        assert rows["boto3"] == [1, 0]


HTMX = {"HTTP_HX_REQUEST": "true"}


class TestHtmxPaging:
    """Paging swaps one table rather than reloading the page."""

    def test_it_returns_only_the_table_htmx_asked_for(self, client, profile):
        response = client.get(
            reverse("probes:stats"),
            HTTP_HX_TARGET="probe-section-symbols",
            **HTMX,
        )
        body = response.content.decode()

        assert response.status_code == 200
        assert "probe-section-symbols" in body
        # A fragment, not a page: no layout around it, and none of the
        # other five tables came along for the ride.
        assert "</html>" not in body
        assert "probe-section-settings" not in body

    def test_without_htmx_the_same_url_renders_the_whole_page(self, client, profile):
        response = client.get(reverse("probes:stats"), {"symbols": 1})

        assert "</html>" in response.content.decode()
        assert len(response.context["sections"]) == 6

    def test_a_target_we_do_not_recognise_is_a_404(self, client, profile):
        response = client.get(
            reverse("probes:stats"), HTTP_HX_TARGET="probe-section-nope", **HTMX
        )

        assert response.status_code == 404

    def test_a_target_that_is_not_a_section_renders_the_page(self, client, profile):
        """Something else on the page asking for a swap is not our business."""
        response = client.get(
            reverse("probes:stats"), HTTP_HX_TARGET="search-results", **HTMX
        )

        assert "</html>" in response.content.decode()


class TestSectionPages:
    """Each table also gets a page of its own, with search."""

    @pytest.mark.parametrize(
        "section", ["libraries", "patterns", "settings", "gone", "symbols", "deps"]
    )
    def test_every_section_has_its_own_page(self, client, profile, section):
        response = client.get(reverse("probes:section", kwargs={"section": section}))

        assert response.status_code == 200
        assert response.context["section"]["paginator"] is not None

    def test_it_links_back_from_the_overview(self, client, profile):
        response = client.get(reverse("probes:stats"))
        urls = {section["url"] for section in response.context["sections"]}

        assert urls == {
            reverse("probes:section", kwargs={"section": param})
            for param in [
                "libraries",
                "patterns",
                "settings",
                "gone",
                "symbols",
                "deps",
            ]
        }

    def test_an_unknown_section_is_a_404(self, client, profile):
        response = client.get(reverse("probes:section", kwargs={"section": "nope"}))

        assert response.status_code == 404

    def test_search_narrows_the_rows(self, client, profile):
        url = reverse("probes:section", kwargs={"section": "symbols"})

        everything = client.get(url).context["section"]["paginator"].count
        matching = client.get(url, {"q": "ugettext"}).context["section"]
        labels = [row["label"] for row in matching["rows"]]

        assert matching["paginator"].count < everything
        assert labels == ["django.utils.translation.ugettext_lazy"]

    def test_search_ignores_case(self, client, profile):
        url = reverse("probes:section", kwargs={"section": "symbols"})

        assert client.get(url, {"q": "UGETTEXT"}).context["section"]["rows"]

    def test_search_that_matches_nothing_says_so(self, client, profile):
        url = reverse("probes:section", kwargs={"section": "symbols"})
        response = client.get(url, {"q": "zzzznope"})

        assert response.status_code == 200
        assert response.context["section"]["rows"] == []
        assert "Nothing found." in response.content.decode()

    def test_searching_over_htmx_returns_just_the_table(self, client, profile):
        response = client.get(
            reverse("probes:section", kwargs={"section": "symbols"}),
            {"q": "ugettext"},
            HTTP_HX_TARGET="probe-section-page",
            **HTMX,
        )
        body = response.content.decode()

        assert "</html>" not in body
        assert "ugettext_lazy" in body

    def test_paging_keeps_the_search(self, client, profile):
        """Or page two of a search would quietly be page two of everything."""
        url = reverse("probes:section", kwargs={"section": "symbols"})
        section = client.get(url, {"q": "django", "page": 1}).context["section"]

        for link in [section["next_url"], section["last_url"]]:
            if link:
                assert "q=django" in link


class TestVersionOrder:
    def test_newest_cycle_first(self, client, profile):
        """Reading starts at the top, and the current releases matter most."""
        response = client.get(reverse("probes:stats"))
        labels = [row.label for row in response.context["django_versions"]]

        assert labels == ["5.2", "5.1"]


class TestRemovalFilter:
    """The gone table filters by the Django version that dropped the API."""

    def url(self):
        return reverse("probes:section", kwargs={"section": "gone"})

    def test_it_offers_only_versions_something_hits(self, client, catalogued):
        """A filter that can return nothing is a filter nobody should see."""
        facets = client.get(self.url()).context["facets"]
        offered = {facet["label"] for facet in facets} - {"All"}

        # The fixture uses ugettext_lazy, which went in 4.0, and nothing
        # that went in any other release.
        assert offered == {"4.0"}
        assert all(facet["count"] for facet in facets)

    def test_choosing_a_version_narrows_the_table(self, client, catalogued):
        response = client.get(self.url(), {"removed_in": "4.0"})
        labels = [row["label"] for row in response.context["section"]["rows"]]

        assert labels == ["django.utils.translation.ugettext_lazy"]

    def test_all_is_chosen_by_default(self, client, profile):
        facets = client.get(self.url()).context["facets"]

        assert facets[0]["label"] == "All"
        assert facets[0]["chosen"] is True

    def test_the_filter_and_the_search_both_apply(self, client, profile):
        response = client.get(self.url(), {"removed_in": "4.0", "q": "zzzznope"})

        assert response.context["section"]["rows"] == []

    def test_sections_without_a_facet_offer_none(self, client, profile):
        response = client.get(reverse("probes:section", kwargs={"section": "symbols"}))

        assert response.context["facets"] == []

    def test_the_table_says_which_version_took_each_symbol(self, client, catalogued):
        response = client.get(self.url())
        row = next(
            row
            for row in response.context["section"]["rows"]
            if row["label"] == "django.utils.translation.ugettext_lazy"
        )

        assert "4.0" in [str(value) for value in row["values"]]

    def test_gone_is_the_last_table_on_the_overview(self, client, profile):
        """It is the most opinionated one, so it reads last."""
        sections = client.get(reverse("probes:stats")).context["sections"]

        assert sections[-1]["param"] == "gone"


class TestKnownRemovals:
    """The curated table of what Django removed and when."""

    def test_a_module_covers_what_lived_in_it(self):
        from probes.removals import removed_in

        assert removed_in("django.core.urlresolvers.reverse") == "2.0"

    def test_an_exact_entry_wins_over_a_prefix(self):
        from probes.removals import removed_in

        assert removed_in("django.conf.urls.url") == "4.0"
        assert removed_in("django.conf.urls.patterns") == "1.10"

    def test_what_we_do_not_know_stays_blank(self):
        """A guessed version would be a wrong fact on a page people trust."""
        from probes.removals import removed_in

        assert removed_in("django.core.mail.outbox.append") == ""
        assert removed_in("django.db.models.CharField") == ""

    def test_curation_in_the_catalogue_wins(self, profile):
        import django

        from probes import stats
        from probes.models import ProbeSymbol

        baker.make(
            ProbeSymbol,
            kind=ProbeSymbol.Kind.SYMBOL,
            library="django",
            name="django.utils.translation.ugettext_lazy",
            removed_in="9.9",
            missing=True,
            checked_against=django.get_version(),
        )
        cache.clear()

        row = next(
            row
            for row in stats.unresolved_rows()
            if row.label == "django.utils.translation.ugettext_lazy"
        )
        assert row.note == "9.9"


class TestGoneRollupReadsTheCatalogue:
    """The page must not import a module to answer a request.

    Resolving each dotted path live meant 4,765 imports on a cache miss
    against production data, which timed the page out.
    """

    def test_it_reports_what_the_catalogue_marked_missing(self, catalogued):
        from probes import stats

        assert [row.label for row in stats.unresolved_rows()] == [
            "django.utils.translation.ugettext_lazy"
        ]

    def test_it_imports_nothing(self, catalogued, monkeypatch):
        import importlib

        from probes import stats

        def explode(*args, **kwargs):
            raise AssertionError("a page request tried to import a module")

        monkeypatch.setattr(importlib, "import_module", explode)
        stats.unresolved_rows()

    def test_an_unchecked_catalogue_reports_nothing_rather_than_guessing(self, profile):
        """Empty is honest; a rebuild fills it in."""
        from probes import stats

        cache.clear()
        assert stats.unresolved_rows() == []

    def test_a_check_against_another_django_is_not_reused(self, profile):
        from probes.models import ProbeSymbol

        baker.make(
            ProbeSymbol,
            kind=ProbeSymbol.Kind.SYMBOL,
            library="django",
            name="django.utils.translation.ugettext_lazy",
            missing=True,
            checked_against="4.2",
        )
        cache.clear()

        from probes import stats

        assert stats.unresolved_rows() == []


class TestResolvingAwkwardNames:
    """Reading an attribute can run code that fails on its own account."""

    def test_an_import_error_behind_an_attribute_is_not_a_removal(self):
        """django.contrib.gis does this when GEOS is not installed."""
        from probes import stats

        class Hostile:
            def __getattr__(self, name):
                raise ImportError("Could not find the GEOS library")

        module = types.ModuleType("probes_fake_module")
        module.gis = Hostile()
        sys.modules["probes_fake_module"] = module
        try:
            stats.resolves.cache_clear()
            assert stats.resolves("probes_fake_module.gis.GEOSGeometry") is True
        finally:
            del sys.modules["probes_fake_module"]
            stats.resolves.cache_clear()

    def test_a_name_that_is_really_absent_is_still_a_removal(self):
        from probes import stats

        stats.resolves.cache_clear()
        assert stats.resolves("django.utils.translation.ugettext_lazy") is False
        assert stats.resolves("django.utils.translation.gettext_lazy") is True

    def test_gis_names_survive_a_missing_gdal(self):
        """Importing django.contrib.gis raises when GDAL is absent.

        The walk up the dotted path then reaches django.contrib.gis.db,
        which imports fine but has no `models` attribute until the
        submodule is imported, so the name looked removed.
        """
        from probes import stats

        stats.resolves.cache_clear()
        assert stats.resolves("django.contrib.gis.db.models.GeometryField") is True

    def test_a_dependency_of_its_own_is_not_a_removal(self, monkeypatch):
        from probes import stats

        def missing_dependency(name):
            raise ModuleNotFoundError("No module named 'nowhere'", name="nowhere")

        monkeypatch.setattr(stats.importlib, "import_module", missing_dependency)
        stats.resolves.cache_clear()
        try:
            assert stats.resolves("probes_fake_package.thing") is True
        finally:
            stats.resolves.cache_clear()
