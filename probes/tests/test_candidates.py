"""Candidate rows: written by discovery, filled from PyPI, decided in the admin."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import Mock, patch

import httpx2
import pytest
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import User
from django.contrib.messages.storage.fallback import FallbackStorage
from django.core.management import call_command
from django.test import RequestFactory
from model_bakery import baker

from package.models import Category, Package
from package.pypi import PyPIPackage
from probes import candidates
from probes.admin import CandidateAdmin
from probes.discovery import Discovered, Discovery
from probes.models import Candidate

pytestmark = pytest.mark.django_db

WHEN = datetime(2026, 11, 7, 18, 45, tzinfo=UTC)


def row(name, **overrides):
    fields = {
        "name": name,
        "first_upload": WHEN,
        "last_upload": WHEN,
        "version": "0.1.0",
        "home_page": "",
        "summary": f"{name} does things",
    }
    fields.update(overrides)
    return Discovered(**fields)


def pypi_json(name, **info):
    data = {
        "name": name,
        "version": "0.1.91",
        "summary": "Open-source AI lead finder",
        "author": "OpenOutreach",
        "author_email": "hello@example.com",
        "requires_dist": ["Django>=5.0", "httpx"],
        "project_urls": {"Source": f"https://github.com/eracle/{name}"},
        "description": "x" * 50_000,
    }
    data.update(info)
    return {
        "info": data,
        "urls": [],
        "releases": {
            "0.1.0": [{"upload_time_iso_8601": "2026-10-20T10:00:00Z"}],
            "0.1.91": [
                {"upload_time_iso_8601": "2026-11-07T00:11:24Z"},
                {"upload_time_iso_8601": "2026-11-07T00:11:30Z"},
            ],
        },
    }


class FakePyPI:
    def __init__(self, projects):
        self.projects = projects
        self.calls = []

    def fetch_package(self, name):
        self.calls.append(name)
        if name not in self.projects:
            response = Mock(status_code=404)
            raise httpx2.HTTPStatusError("404", request=Mock(), response=response)
        return PyPIPackage(self.projects[name])


class TestRecord:
    def test_new_names_become_candidates(self):
        found = Discovery(tracked=[], new=[row("karni-ai"), row("karni-charts")])

        result = candidates.record(found, "django")

        assert result.created == 2
        assert set(Candidate.objects.values_list("name", flat=True)) == {
            "karni-ai",
            "karni-charts",
        }
        saved = Candidate.objects.get(name="karni-ai")
        assert saved.framework == "django"
        assert saved.status == Candidate.Status.NEW
        assert saved.last_upload == WHEN
        assert saved.last_seen is not None

    def test_a_second_run_refreshes_but_keeps_the_decision(self):
        candidates.record(Discovery(tracked=[], new=[row("spammy")]), "django")
        Candidate.objects.filter(name="spammy").update(status=Candidate.Status.REJECTED)

        later = row("spammy", version="0.2.0", last_upload=WHEN.replace(day=9))
        result = candidates.record(Discovery(tracked=[], new=[later]), "django")

        assert result.created == 0
        assert result.refreshed == 1
        saved = Candidate.objects.get(name="spammy")
        assert saved.status == Candidate.Status.REJECTED
        assert saved.version == "0.2.0"
        assert saved.last_upload.day == 9

    def test_names_we_already_index_link_their_stale_candidate(self):
        package = baker.make(
            Package, slug="x", title="x", repo_url="https://github.com/x/x"
        )
        candidates.record(Discovery(tracked=[], new=[row("x")]), "django")

        result = candidates.record(
            Discovery(tracked=[(row("x"), package.pk)], new=[]), "django"
        )

        assert result.linked == 1
        saved = Candidate.objects.get(name="x")
        assert saved.status == Candidate.Status.IMPORTED
        assert saved.package == package

    def test_tracked_names_without_a_candidate_create_nothing(self):
        package = baker.make(
            Package, slug="y", title="y", repo_url="https://github.com/y/y"
        )
        candidates.record(Discovery(tracked=[(row("y"), package.pk)], new=[]), "django")
        assert Candidate.objects.count() == 0


class TestEnrich:
    def test_it_keeps_the_small_parts_of_the_pypi_json(self):
        candidate = baker.make(Candidate, name="openoutreach", pypi_data={})
        client = FakePyPI({"openoutreach": pypi_json("openoutreach")})

        assert candidates.enrich(candidate, client=client)

        candidate.refresh_from_db()
        assert "description" not in candidate.pypi_data["info"]
        assert candidate.author == "OpenOutreach"
        assert candidate.requires_dist == ["Django>=5.0", "httpx"]
        assert candidate.release_count == 2
        assert candidate.first_release.startswith("2026-10-20")
        assert candidate.repo_url == "https://github.com/eracle/openoutreach"
        assert candidate.version == "0.1.91"
        assert candidate.pypi_fetched_at is not None
        assert candidate.depends_on_django is True

    def test_a_package_that_does_not_need_django_says_so(self):
        candidate = baker.make(Candidate, name="mailhive", pypi_data={})
        client = FakePyPI({"mailhive": pypi_json("mailhive", requires_dist=["httpx"])})
        candidates.enrich(candidate, client=client)
        candidate.refresh_from_db()
        assert candidate.depends_on_django is False

    def test_no_data_yet_is_unknown_not_false(self):
        assert baker.make(Candidate, pypi_data={}).depends_on_django is None

    def test_a_404_leaves_the_row_alone(self):
        candidate = baker.make(Candidate, name="gone", pypi_data={})
        assert not candidates.enrich(candidate, client=FakePyPI({}))
        candidate.refresh_from_db()
        assert candidate.pypi_data == {}
        assert candidate.pypi_fetched_at is None

    def test_enrich_missing_only_touches_rows_without_data(self):
        baker.make(Candidate, name="a", pypi_data={}, last_upload=WHEN)
        baker.make(Candidate, name="b", pypi_data={"info": {}}, last_upload=WHEN)
        baker.make(Candidate, name="c", pypi_data={}, last_upload=WHEN)
        client = FakePyPI({"a": pypi_json("a"), "c": pypi_json("c")})

        assert candidates.enrich_missing(client=client) == 2
        assert sorted(client.calls) == ["a", "c"]

    def test_enrich_missing_can_be_capped(self):
        for name in "abc":
            baker.make(Candidate, name=name, pypi_data={}, last_upload=WHEN)
        client = FakePyPI({n: pypi_json(n) for n in "abc"})
        assert candidates.enrich_missing(limit=2, client=client) == 2


class TestImporterLink:
    def test_importing_a_name_marks_its_candidate(self):
        apps = Category.objects.get_or_create(slug="apps", defaults={"title": "App"})[0]
        baker.make(Candidate, name="django-thing", pypi_data={})
        from package.importer import import_from_pypi

        with patch(
            "package.repos.github.GitHubHandler.fetch_metadata",
            side_effect=lambda package, save=True: package,
        ):
            result = import_from_pypi(
                "django-thing",
                category=apps,
                client=FakePyPI({"django-thing": pypi_json("django-thing")}),
            )

        assert result.created
        saved = Candidate.objects.get(name="django-thing")
        assert saved.status == Candidate.Status.IMPORTED
        assert saved.package == result.package


class TestCommand:
    def test_discover_records_candidates_by_default(self):
        from probes.tests.test_discovery import FakeClient, _row

        client = FakeClient(rows=[_row("django-newthing")])
        with (
            patch("probes.discovery.bigquery_client", return_value=client),
            patch("probes.candidates.enrich_missing", return_value=0) as enrich,
        ):
            call_command("pypi_discover", "--framework", "django", "--days", "7")

        assert Candidate.objects.filter(name="django-newthing").exists()
        enrich.assert_called_once()

    def test_no_record_only_prints(self):
        from probes.tests.test_discovery import FakeClient, _row

        client = FakeClient(rows=[_row("django-newthing")])
        with patch("probes.discovery.bigquery_client", return_value=client):
            call_command(
                "pypi_discover", "--framework", "django", "--days", "7", "--no-record"
            )

        assert Candidate.objects.count() == 0


@pytest.fixture()
def admin_request():
    user = User.objects.create_superuser("admin", "a@example.com", "pw")
    request = RequestFactory().post("/admin/")
    request.user = user
    request.session = {}
    request._messages = FallbackStorage(request)
    return request


class TestAdminActions:
    def test_reject_records_who_and_when(self, admin_request):
        baker.make(Candidate, name="spam", pypi_data={})
        model_admin = CandidateAdmin(Candidate, AdminSite())

        model_admin.reject(admin_request, Candidate.objects.all())

        saved = Candidate.objects.get(name="spam")
        assert saved.status == Candidate.Status.REJECTED
        assert saved.reviewed_by == admin_request.user
        assert saved.reviewed_at is not None

    def test_approve_runs_the_importer_and_links_the_package(self, admin_request):
        Category.objects.get_or_create(slug="apps", defaults={"title": "App"})
        baker.make(Candidate, name="django-good", pypi_data={})
        model_admin = CandidateAdmin(Candidate, AdminSite())

        with (
            patch("probes.admin.import_from_pypi") as importer,
        ):
            package = baker.make(
                Package,
                slug="django-good",
                title="g",
                repo_url="https://github.com/g/g",
            )
            importer.return_value = Mock(
                created=True, status="created", package=package
            )
            model_admin.approve_and_import(admin_request, Candidate.objects.all())

        importer.assert_called_once()
        saved = Candidate.objects.get(name="django-good")
        assert saved.status == Candidate.Status.APPROVED
        assert saved.reviewed_by == admin_request.user

    def test_approving_something_that_cannot_import_warns(self, admin_request):
        Category.objects.get_or_create(slug="apps", defaults={"title": "App"})
        baker.make(Candidate, name="norepo", pypi_data={})
        model_admin = CandidateAdmin(Candidate, AdminSite())

        with patch("probes.admin.import_from_pypi") as importer:
            importer.return_value = Mock(
                created=False, status="no_repo", package=None, note="no repository"
            )
            model_admin.approve_and_import(admin_request, Candidate.objects.all())

        saved = Candidate.objects.get(name="norepo")
        assert saved.status == Candidate.Status.APPROVED
        assert any("norepo" in str(m) for m in admin_request._messages)

    def test_imported_rows_are_not_decided_again(self, admin_request):
        baker.make(
            Candidate, name="done", status=Candidate.Status.IMPORTED, pypi_data={}
        )
        model_admin = CandidateAdmin(Candidate, AdminSite())
        model_admin.reject(admin_request, Candidate.objects.all())
        assert Candidate.objects.get(name="done").status == Candidate.Status.IMPORTED
