"""Working out what a distribution is imported as."""

import pytest
from django.core.management import call_command
from model_bakery import baker

from probes.imports import canonical_name, detect_import_names, normalize
from probes.models import Library

pytestmark = pytest.mark.django_db


def make_checkout(root, *, packages=(), modules=(), under=""):
    """A checkout with some importable things in it."""
    base = root / under if under else root
    base.mkdir(parents=True, exist_ok=True)
    (root / ".git").mkdir(exist_ok=True)
    for name in packages:
        (base / name).mkdir(parents=True, exist_ok=True)
        (base / name / "__init__.py").write_text("")
    for name in modules:
        (base / f"{name}.py").write_text("")
    return root


class TestDetectImportNames:
    def test_the_obvious_case(self, tmp_path):
        make_checkout(tmp_path, packages=["taggit"])

        assert detect_import_names(tmp_path, pypi_name="django-taggit") == ["taggit"]

    def test_the_distribution_name_breaks_the_tie(self, tmp_path):
        """A repo ships its package and a demo app beside it."""
        make_checkout(tmp_path, packages=["sample_taggit", "taggit"])

        names = detect_import_names(tmp_path, pypi_name="django-taggit")

        assert names[0] == "taggit"
        assert "sample_taggit" in names

    def test_a_package_under_src_beats_a_script_at_the_root(self, tmp_path):
        """django-htmx keeps a download_htmx.py helper at the root."""
        make_checkout(tmp_path, modules=["download_htmx"])
        make_checkout(tmp_path, packages=["django_htmx"], under="src")

        assert detect_import_names(tmp_path, pypi_name="django-htmx")[0] == (
            "django_htmx"
        )

    def test_root_scripts_are_not_import_names(self, tmp_path):
        make_checkout(tmp_path, packages=["ninja"], modules=["noxfile", "conftest"])

        assert detect_import_names(tmp_path, pypi_name="django-ninja") == ["ninja"]

    def test_tests_and_docs_are_not_the_package(self, tmp_path):
        make_checkout(tmp_path, packages=["corsheaders", "tests", "docs", "example"])

        assert detect_import_names(tmp_path, pypi_name="django-cors-headers") == [
            "corsheaders"
        ]

    def test_a_module_is_used_when_there_is_no_package(self, tmp_path):
        """Plenty of small packages are a single file."""
        make_checkout(tmp_path, modules=["easydump"])

        assert detect_import_names(tmp_path, pypi_name="django-easydump") == [
            "easydump"
        ]

    def test_an_empty_checkout_detects_nothing(self, tmp_path):
        assert detect_import_names(tmp_path, pypi_name="whatever") == []


class TestNames:
    def test_the_naive_guess(self):
        assert normalize("django-debug-toolbar") == "django_debug_toolbar"

    def test_canonical_names_collapse_case_and_separators(self):
        assert canonical_name("Django") == "django"
        assert canonical_name("djangorestframework") == "djangorestframework"
        assert canonical_name("zope.interface") == "zope-interface"


class TestBuildProbeLibraries:
    @pytest.fixture()
    def package(self, settings, tmp_path):
        settings.PACKAGE_REPO_ROOT = tmp_path
        package = baker.make(
            "package.Package",
            slug="django-debug-toolbar",
            title="django-debug-toolbar",
            repo_url="https://github.com/django-commons/django-debug-toolbar",
            pypi_url="https://pypi.org/project/django-debug-toolbar/",
            score=10,
        )
        make_checkout(tmp_path / "django-debug-toolbar", packages=["debug_toolbar"])
        return package

    def test_it_records_what_the_checkout_says(self, package):
        call_command("build_probe_libraries")

        library = Library.objects.get(pypi_name="django-debug-toolbar")
        assert library.import_name == "debug_toolbar"
        assert library.source == Library.Source.CHECKOUT
        assert library.names_differ

    def test_no_checkout_means_no_row(self, settings, tmp_path):
        """It used to write django_nothing here, which is a made up fact."""
        settings.PACKAGE_REPO_ROOT = tmp_path
        baker.make(
            "package.Package",
            slug="django-nothing",
            title="django-nothing",
            repo_url="https://github.com/x/django-nothing",
            pypi_url="https://pypi.org/project/django-nothing/",
            score=1,
        )

        call_command("build_probe_libraries")

        assert not Library.objects.filter(pypi_name="django-nothing").exists()

    def test_a_rebuild_leaves_the_scan_toggle_alone(self, package):
        """Toggling a library on is a decision, not derived data."""
        call_command("build_probe_libraries")
        Library.objects.filter(pypi_name="django-debug-toolbar").update(scan=True)

        call_command("build_probe_libraries")

        assert Library.objects.get(pypi_name="django-debug-toolbar").scan is True

    def test_a_dry_run_writes_nothing(self, package):
        call_command("build_probe_libraries", "--dry-run")

        assert not Library.objects.filter(pypi_name="django-debug-toolbar").exists()


class TestWhichLibrariesAreScannedFor:
    def test_django_comes_first(self):
        baker.make(
            "probes.Library", pypi_name="wagtail", import_name="wagtail", scan=True
        )

        assert Library.scan_for()[0] == "django"

    def test_only_the_ones_toggled_on(self):
        baker.make(
            "probes.Library", pypi_name="celery", import_name="celery", scan=None
        )
        baker.make("probes.Library", pypi_name="ninja", import_name="ninja", scan=False)
        baker.make(
            "probes.Library", pypi_name="wagtail", import_name="wagtail", scan=True
        )

        assert Library.scan_for() == ("django", "wagtail")

    def test_the_scan_uses_them(self, settings, tmp_path):
        settings.PACKAGE_REPO_ROOT = tmp_path
        baker.make(
            "package.Package",
            slug="a",
            title="a",
            repo_url="https://github.com/x/a",
            pypi_url="https://pypi.org/project/a/",
            score=1,
        )
        baker.make(
            "probes.Library",
            pypi_name="djangorestframework",
            import_name="rest_framework",
            scan=True,
        )
        (tmp_path / "a" / ".git").mkdir(parents=True)
        (tmp_path / "a" / "views.py").write_text(
            "from rest_framework.views import APIView\n"
        )

        call_command("scan_package_repos", "--totals-only")

        from probes.models import PackageProbe

        profile = PackageProbe.objects.get(package__slug="a")
        assert "rest_framework" in profile.libraries
        assert profile.library_counts["rest_framework"] >= 1


class TestSourceDirsArePooled:
    """A package under src/ beats a demo project at the root."""

    def test_the_root_demo_does_not_win(self, tmp_path):
        """django-oscar ships `sandbox` at the root and `oscar` in src."""
        for name in ["sandbox", "tests"]:
            (tmp_path / name).mkdir()
            (tmp_path / name / "__init__.py").touch()
        (tmp_path / "src" / "oscar").mkdir(parents=True)
        (tmp_path / "src" / "oscar" / "__init__.py").touch()

        assert detect_import_names(tmp_path, pypi_name="django-oscar")[0] == "oscar"

    def test_a_root_package_still_wins_when_it_is_the_match(self, tmp_path):
        (tmp_path / "taggit").mkdir()
        (tmp_path / "taggit" / "__init__.py").touch()
        (tmp_path / "src" / "helpers").mkdir(parents=True)
        (tmp_path / "src" / "helpers" / "__init__.py").touch()

        assert detect_import_names(tmp_path, pypi_name="django-taggit")[0] == "taggit"
