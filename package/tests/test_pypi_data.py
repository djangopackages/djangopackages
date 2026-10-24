"""Dependents and friends, read out of a pypi-data dump."""

import sqlite3
from unittest.mock import patch

import pytest
from django.core.management import call_command
from model_bakery import baker

from package import pypi_data
from package.models import Package

pytestmark = pytest.mark.django_db


@pytest.fixture
def dump(tmp_path):
    """A pypi.db with the tables and spellings the real one has."""
    path = tmp_path / "pypi.db"
    con = sqlite3.connect(path)
    con.executescript(
        """
        create table packages (name, version, scorecard_overall, has_vulnerabilities,
                               last_uploaded_at);
        create table deps (package_name, extra, dep_name, dep_specifier);
        insert into packages values
            ('django-debug-toolbar', '5.0', 7.2, 0, '2026-06-19T00:21:23'),
            ('django-nh3', '0.1', null, null, '2026-01-01T00:00:00'),
            ('Django_Fancy', '1.0', 3.0, 1, '2020-01-01T00:00:00');
        insert into deps values
            ('app-one', null, 'django-debug-toolbar', '>=4'),
            ('app-one', null, 'Django', ''),
            ('app-two', null, 'Django-Debug-Toolbar', ''),
            ('app-two', 'dev', 'django-debug-toolbar', ''),
            ('app-three', null, 'django_debug_toolbar', ''),
            ('django-debug-toolbar', null, 'django', '>=4.2'),
            ('django-debug-toolbar', null, 'sqlparse', ''),
            ('django-debug-toolbar', 'test', 'pytest', ''),
            ('django-fancy', null, 'django', '');
        """
    )
    con.commit()
    con.close()
    return path


def _package(slug, pypi_name=None):
    return baker.make(
        Package,
        slug=slug,
        repo_url=f"https://github.com/x/{slug}",
        pypi_url=f"https://pypi.org/project/{pypi_name or slug}/",
    )


class TestReadMetrics:
    def test_dependents_count_distinct_projects_whatever_the_spelling(self, dump):
        found = pypi_data.read_metrics(dump, {"django-debug-toolbar"})

        m = found["django-debug-toolbar"]
        # app-one, app-two (once, despite two rows) and app-three.
        assert m.dependents == 3
        # django and sqlparse; the test extra does not count.
        assert m.dependencies == 2
        assert m.scorecard == 7.2
        assert m.has_vulnerabilities is False

    def test_project_names_are_normalised_both_ways(self, dump):
        found = pypi_data.read_metrics(dump, {"django-fancy"})

        assert found["django-fancy"].has_vulnerabilities is True
        assert found["django-fancy"].dependencies == 1

    def test_nulls_stay_null(self, dump):
        found = pypi_data.read_metrics(dump, {"django-nh3"})

        m = found["django-nh3"]
        assert (m.dependents, m.dependencies) == (0, 0)
        assert m.scorecard is None
        assert m.has_vulnerabilities is None

    def test_unknown_names_are_simply_absent(self, dump):
        assert pypi_data.read_metrics(dump, {"nope"}) == {}


class TestSync:
    def test_writes_metrics_onto_our_packages(self, dump):
        toolbar = _package("django-debug-toolbar", "Django-Debug-Toolbar")
        gone = _package("django-gone")
        baker.make(
            Package,
            slug="no-pypi",
            repo_url="https://github.com/x/no-pypi",
            pypi_url="",
        )

        outcome = pypi_data.sync(path=dump)

        assert (outcome.packages, outcome.matched) == (2, 1)
        toolbar.refresh_from_db()
        assert toolbar.pypi_dependents == 3
        assert toolbar.pypi_dependencies == 2
        assert toolbar.pypi_scorecard == 7.2
        assert toolbar.pypi_has_vulnerabilities is False
        assert toolbar.pypi_data_synced_at is not None
        gone.refresh_from_db()
        assert gone.pypi_dependents is None
        assert gone.pypi_data_synced_at is not None

    def test_a_package_the_dump_dropped_is_cleared(self, dump):
        gone = _package("django-gone")
        Package.objects.filter(pk=gone.pk).update(pypi_dependents=40)

        pypi_data.sync(path=dump)

        gone.refresh_from_db()
        assert gone.pypi_dependents is None

    def test_dry_run_saves_nothing(self, dump):
        toolbar = _package("django-debug-toolbar")

        outcome = pypi_data.sync(path=dump, save=False)

        assert outcome.matched == 1
        toolbar.refresh_from_db()
        assert toolbar.pypi_dependents is None

    def test_the_download_is_skipped_when_the_release_is_on_disk(
        self, dump, settings, tmp_path
    ):
        settings.PYPI_DATA_ROOT = tmp_path
        (tmp_path / pypi_data.TAG_FILE).write_text("2026.07.21\n")
        release = pypi_data.Release("2026.07.21", "https://x/pypi.db.gz", "")

        with (
            patch("package.pypi_data.latest_release", return_value=release),
            patch("package.pypi_data.download") as download,
        ):
            outcome = pypi_data.sync()

        download.assert_not_called()
        assert outcome.downloaded is False
        assert outcome.release == "2026.07.21"

    def test_a_new_release_is_downloaded(self, dump, settings, tmp_path):
        settings.PYPI_DATA_ROOT = tmp_path
        (tmp_path / pypi_data.TAG_FILE).write_text("2026.01.01\n")
        dump.rename(tmp_path / pypi_data.DB_NAME)
        release = pypi_data.Release("2026.07.21", "https://x/pypi.db.gz", "")

        with (
            patch("package.pypi_data.latest_release", return_value=release),
            patch("package.pypi_data.download") as download,
        ):
            outcome = pypi_data.sync()

        download.assert_called_once_with(release)
        assert outcome.downloaded is True


class TestCommand:
    def test_reads_a_local_database(self, dump, capsys):
        toolbar = _package("django-debug-toolbar")

        call_command("pypi_data_sync", "--db", str(dump))

        toolbar.refresh_from_db()
        assert toolbar.pypi_dependents == 3
        assert "1 of 1" in capsys.readouterr().out

    def test_the_job_is_scheduled(self):
        from core.management.commands.init_scheduled_jobs import JOBS

        assert JOBS["pypi-data"]["args"] == ("pypi_data_sync",)


class TestPackagePage:
    def test_dependents_show_when_known(self, client):
        package = _package("django-debug-toolbar")
        Package.objects.filter(pk=package.pk).update(pypi_dependents=1234)

        response = client.get(package.get_absolute_url())

        assert b"1,234" in response.content
        assert b"PyPI projects that require this package" in response.content

    def test_nothing_shows_before_the_first_sync(self, client):
        package = _package("django-debug-toolbar")

        response = client.get(package.get_absolute_url())

        assert b"PyPI projects that require this package" not in response.content
