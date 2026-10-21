"""The symbol catalogue, and what a rebuild is allowed to touch."""

import pytest
from django.core.management import call_command
from model_bakery import baker

from probes.models import PackageProbe, ProbeSymbol

pytestmark = pytest.mark.django_db


@pytest.fixture()
def profiles():
    """Two packages, one of which uses an API Django has removed."""
    for slug, symbols in (
        (
            "modern",
            [
                {"symbol": "django.urls.path", "count": 4, "library": "django"},
                {
                    "symbol": "django.conf.settings.DEBUG",
                    "count": 2,
                    "library": "django",
                },
            ],
        ),
        (
            "ancient",
            [
                {
                    "symbol": "django.utils.translation.ugettext_lazy",
                    "count": 9,
                    "library": "django",
                },
                {"symbol": "django.urls.path", "count": 1, "library": "django"},
            ],
        ),
    ):
        package = baker.make(
            "package.Package",
            slug=slug,
            title=slug,
            repo_url=f"https://github.com/x/{slug}",
        )
        baker.make(
            PackageProbe,
            package=package,
            symbols=symbols,
            patterns=[{"pattern": "probe:queryset_filter", "count": 3}],
            libraries=["django"],
        )


class TestBuildProbeCatalog:
    def test_it_counts_packages_and_uses(self, profiles):
        call_command("build_probe_catalog")

        row = ProbeSymbol.objects.get(
            kind=ProbeSymbol.Kind.SYMBOL, name="django.urls.path"
        )
        assert row.packages == 2
        assert row.uses == 5
        assert row.library == "django"

    def test_settings_and_patterns_get_their_own_kinds(self, profiles):
        call_command("build_probe_catalog")

        assert ProbeSymbol.objects.filter(
            kind=ProbeSymbol.Kind.SETTING, name="DEBUG"
        ).exists()
        assert ProbeSymbol.objects.filter(
            kind=ProbeSymbol.Kind.PATTERN, name="queryset_filter"
        ).exists()

    def test_a_rebuild_never_overwrites_curation(self, profiles):
        """The whole point of the table: our notes outlive the counts."""
        call_command("build_probe_catalog")
        ProbeSymbol.objects.filter(
            name="django.utils.translation.ugettext_lazy"
        ).update(
            deprecated=True, deprecated_in="3.0", removed_in="4.0", notes="use gettext"
        )

        call_command("build_probe_catalog")

        row = ProbeSymbol.objects.get(name="django.utils.translation.ugettext_lazy")
        assert row.deprecated is True
        assert row.removed_in == "4.0"
        assert row.notes == "use gettext"
        assert row.uses == 9

    def test_a_dry_run_writes_nothing(self, profiles):
        call_command("build_probe_catalog", "--dry-run")

        assert not ProbeSymbol.objects.exists()

    def test_prune_keeps_anything_we_annotated(self, profiles):
        call_command("build_probe_catalog")
        ProbeSymbol.objects.create(
            name="django.utils.six", library="django", removed_in="3.0"
        )
        ProbeSymbol.objects.create(name="django.gone.unloved", library="django")

        call_command("build_probe_catalog", "--prune")

        assert ProbeSymbol.objects.filter(name="django.utils.six").exists()
        assert not ProbeSymbol.objects.filter(name="django.gone.unloved").exists()


class TestStatus:
    def test_a_removal_version_reads_as_gone(self):
        row = ProbeSymbol(name="x", removed_in="4.0")

        assert row.gone
        assert row.status == "removed in 4.0"

    def test_a_live_symbol_has_no_status(self):
        row = ProbeSymbol(name="x")

        assert not row.gone
        assert row.status == ""


@pytest.mark.django_db
class TestTheSeededLibrary:
    """The initial migration creates the one library we always scan for."""

    def test_django_is_there_and_switched_on(self):
        from probes.models import Library

        django = Library.objects.get(pypi_name="django")

        assert django.import_name == "django"
        assert django.scan is True
        assert django.source == Library.Source.MANUAL

    def test_scans_pick_it_up_without_anyone_configuring_anything(self):
        from probes.models import Library

        assert Library.scan_for() == ("django",)
