"""`pypi_discover` and the BigQuery query behind it, with a fake client."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest
from django.core.management import call_command
from django.test import override_settings
from model_bakery import baker

from probes import discovery

pytestmark = pytest.mark.django_db


class FakeJob:
    def __init__(self, rows, scanned):
        self._rows = rows
        self.total_bytes_processed = scanned

    def result(self):
        return iter(self._rows)


class FakeClient:
    """Records the query it was given and answers with canned rows."""

    def __init__(self, rows=(), scanned=3 * 1024**3):
        self.rows = list(rows)
        self.scanned = scanned
        self.calls = []

    def query(self, sql, job_config=None):
        self.calls.append((sql, job_config))
        return FakeJob(self.rows if not job_config.dry_run else [], self.scanned)


def _row(name, **overrides):
    when = datetime(2026, 10, 20, tzinfo=UTC)
    row = {
        "name": name,
        "first_upload": when,
        "last_upload": when,
        "version": "1.0",
        "home_page": f"https://github.com/x/{name}",
        "summary": f"{name} does things",
        "classifiers": ["Framework :: Django", "Framework :: Django :: 5.2"],
    }
    row.update(overrides)
    return row


class TestBuildQuery:
    def test_it_matches_the_classifier_prefix(self):
        sql, params = discovery.build_query("wagtail", days=7)

        assert "STARTS_WITH(c, @prefix)" in sql
        assert params["prefix"] == "Framework :: Wagtail"
        assert "upload_time >= @since" in sql
        assert "GROUP BY name" in sql

    def test_it_is_cacheable_for_the_whole_day(self):
        # BigQuery skips its cache for CURRENT_TIMESTAMP(), so the cutoff
        # must be a fixed midnight-UTC parameter instead.
        sql, params = discovery.build_query("wagtail", days=7)

        assert "CURRENT_TIMESTAMP" not in sql
        midnight = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
        assert params["since"] == midnight - timedelta(days=7)
        assert discovery.build_query("wagtail", days=7) == (sql, params)

    def test_the_whole_index_has_no_date_filter(self):
        sql, params = discovery.build_query("django-cms", days=None)

        assert "upload_time >=" not in sql
        assert params == {"prefix": "Framework :: Django CMS"}

    def test_every_framework_is_a_django_family(self):
        for prefix in discovery.FRAMEWORKS.values():
            assert prefix.startswith("Framework :: ")
            assert "Django" in prefix or prefix == "Framework :: Wagtail"


class TestDiscover:
    def test_it_splits_rows_by_whether_we_index_them(self):
        baker.make(
            "package.Package",
            slug="django-nanopages",
            pypi_url="https://pypi.org/project/Django_Nanopages/",
            repo_url="https://github.com/x/nanopages",
        )
        client = FakeClient(rows=[_row("django-nanopages"), _row("brand-new-thing")])

        found = discovery.discover("django", 7, client=client)

        assert [row.name for row in found.new] == ["brand-new-thing"]
        assert [(row.name, pk > 0) for row, pk in found.tracked] == [
            ("django-nanopages", True)
        ]
        assert found.bytes_processed == 3 * 1024**3
        assert found.new[0].pypi_url == "https://pypi.org/project/brand-new-thing/"

    def test_it_passes_the_parameters_and_the_byte_cap(self):
        client = FakeClient()

        discovery.discover("wagtail", 30, client=client)

        ((sql, config),) = client.calls
        assert config.dry_run is False
        assert config.maximum_bytes_billed == 20 * 1024**3
        by_name = {p.name: p.value for p in config.query_parameters}
        assert by_name["prefix"] == "Framework :: Wagtail"
        assert by_name["since"].tzinfo is UTC
        types = {p.name: p.type_ for p in config.query_parameters}
        assert types == {"prefix": "STRING", "since": "TIMESTAMP"}

    def test_estimate_is_a_dry_run(self):
        client = FakeClient(scanned=7 * 1024**3)

        assert discovery.estimate("django", None, client=client) == 7 * 1024**3
        ((_, config),) = client.calls
        assert config.dry_run is True

    def test_null_columns_become_empty_strings(self):
        client = FakeClient(
            rows=[_row("x", version=None, home_page=None, summary=None)]
        )

        found = discovery.discover("django", 7, client=client)

        assert (found.new[0].version, found.new[0].home_page, found.new[0].summary) == (
            "",
            "",
            "",
        )

    def test_classifiers_come_back_with_each_row(self):
        client = FakeClient(rows=[_row("x"), _row("y", classifiers=None)])

        found = discovery.discover("django", 7, client=client)

        by_name = {row.name: row.classifiers for row in found.new}
        assert by_name == {
            "x": ("Framework :: Django", "Framework :: Django :: 5.2"),
            "y": (),
        }

    def test_it_selects_the_latest_classifiers(self):
        sql, _ = discovery.build_query("django", days=7)

        assert "AS classifiers" in sql


class TestClient:
    @override_settings(GOOGLE_BIGQUERY_CREDENTIALS="")
    def test_it_refuses_to_run_without_credentials(self):
        with pytest.raises(RuntimeError, match="GOOGLE_BIGQUERY_CREDENTIALS"):
            discovery.bigquery_client()


class TestCommand:
    def test_it_saves_the_csv_under_media(self, tmp_path):
        baker.make(
            "package.Package",
            slug="old",
            pypi_url="https://pypi.org/project/old/",
            repo_url="https://github.com/x/old",
        )
        client = FakeClient(rows=[_row("old"), _row("shiny")])

        with (
            override_settings(MEDIA_ROOT=tmp_path, MEDIA_URL="/media/"),
            patch.object(discovery, "bigquery_client", return_value=client),
        ):
            call_command(
                "pypi_discover", "--framework", "django", "--days", "7", "--csv"
            )

        (path,) = (tmp_path / "pypi-discover").glob("django-7d-*.csv")
        lines = path.read_text().splitlines()
        assert lines[0].startswith("status,name,pypi_url,package_slug,")
        assert lines[1].startswith("new,shiny,https://pypi.org/project/shiny/,,")
        assert lines[2].startswith("indexed,old,https://pypi.org/project/old/,old,")

    def test_the_backfill_csv_is_named_all(self):
        from probes.management.commands.pypi_discover import csv_destination

        with override_settings(MEDIA_ROOT="/data/media"):
            assert csv_destination("wagtail", None).parent == Path(
                "/data/media/pypi-discover"
            )
            assert csv_destination("wagtail", None).name.startswith("wagtail-all-")
            assert csv_destination("wagtail", 30).name.startswith("wagtail-30d-")

    def test_estimate_runs_no_query(self):
        client = FakeClient()
        with patch.object(discovery, "bigquery_client", return_value=client):
            call_command("pypi_discover", "--framework", "wagtail", "--estimate")

        ((_, config),) = client.calls
        assert config.dry_run is True

    def test_an_unknown_framework_is_rejected(self):
        import click

        with pytest.raises(click.BadParameter, match="drf"):
            call_command("pypi_discover", "--framework", "drf")
