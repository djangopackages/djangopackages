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
from probes.admin import CandidateAdmin, FrameworkFilter
from probes.discovery import Discovered, Discovery
from probes.ecosystems import canonical, trimmed
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
        "classifiers": ("Framework :: Django", "Framework :: Django :: 5.2"),
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


ECOSYSTEMS = {
    "repository_url": "https://github.com/eracle/OpenOutreach",
    "downloads": 2247,
    "downloads_period": "last-month",
    "dependent_repos_count": 3,
    "versions_count": 72,
    "first_release_published_at": "2026-08-21T00:00:00.000Z",
    "advisories": [],
    "maintainers": [{"login": "eracle", "packages_count": 2, "html_url": "x"}],
    "repo_metadata": {
        "full_name": "eracle/OpenOutreach",
        "stargazers_count": 3528,
        "forks_count": 400,
        "archived": False,
        "fork": False,
        "created_at": "2016-10-07T12:00:00.000Z",
        "commit_stats": {"total_commits": 900, "total_committers": 20},
        "etag": "drop me",
    },
    "rankings": {"drop": "me"},
}


class FakeEcosystems:
    def __init__(self, records, fail=False, remaining=None):
        self.records = records
        self.fail = fail
        self.calls = []
        self.batches = []
        self.requests = 0
        self.remaining = remaining

    def fetch_package(self, name):
        self.calls.append(name)
        self.requests += 1
        if self.fail:
            raise httpx2.RequestError("down")
        payload = self.records.get(name)
        if payload is None:
            return None
        return trimmed(payload)

    def fetch_packages(self, names):
        names = list(names)
        self.calls.extend(names)
        self.batches.append(names)
        self.requests += 1
        if self.fail:
            raise httpx2.RequestError("down")
        return {
            canonical(name): trimmed(self.records[name])
            for name in names
            if name in self.records
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

        result = candidates.record(found)

        assert result.created == 2
        assert set(Candidate.objects.values_list("name", flat=True)) == {
            "karni-ai",
            "karni-charts",
        }
        saved = Candidate.objects.get(name="karni-ai")
        assert saved.classifiers == [
            "Framework :: Django",
            "Framework :: Django :: 5.2",
        ]
        assert saved.frameworks == ["django"]
        assert saved.status == Candidate.Status.NEW
        assert saved.last_upload == WHEN
        assert saved.last_seen is not None

    def test_a_second_run_refreshes_but_keeps_the_decision(self):
        candidates.record(Discovery(tracked=[], new=[row("spammy")]))
        Candidate.objects.filter(name="spammy").update(status=Candidate.Status.REJECTED)

        later = row("spammy", version="0.2.0", last_upload=WHEN.replace(day=9))
        result = candidates.record(Discovery(tracked=[], new=[later]))

        assert result.created == 0
        assert result.refreshed == 1
        saved = Candidate.objects.get(name="spammy")
        assert saved.status == Candidate.Status.REJECTED
        assert saved.version == "0.2.0"
        assert saved.last_upload.day == 9

    def test_a_later_run_refreshes_the_classifiers(self):
        candidates.record(Discovery(tracked=[], new=[row("wagtail-katex")]))
        wagtail = row(
            "wagtail-katex",
            classifiers=("Framework :: Django", "Framework :: Wagtail :: 7"),
        )

        candidates.record(Discovery(tracked=[], new=[wagtail]))

        saved = Candidate.objects.get(name="wagtail-katex")
        assert saved.frameworks == ["django", "wagtail"]

    def test_names_we_already_index_link_their_stale_candidate(self):
        package = baker.make(
            Package, slug="x", title="x", repo_url="https://github.com/x/x"
        )
        candidates.record(Discovery(tracked=[], new=[row("x")]))

        result = candidates.record(Discovery(tracked=[(row("x"), package.pk)], new=[]))

        assert result.linked == 1
        saved = Candidate.objects.get(name="x")
        assert saved.status == Candidate.Status.IMPORTED
        assert saved.package == package

    def test_tracked_names_without_a_candidate_create_nothing(self):
        package = baker.make(
            Package, slug="y", title="y", repo_url="https://github.com/y/y"
        )
        candidates.record(Discovery(tracked=[(row("y"), package.pk)], new=[]))
        assert Candidate.objects.count() == 0


class TestEnrich:
    def test_it_keeps_the_small_parts_of_the_pypi_json(self):
        candidate = baker.make(Candidate, name="openoutreach", pypi_data={})
        client = FakePyPI({"openoutreach": pypi_json("openoutreach")})

        assert candidates.enrich(
            candidate, client=client, ecosystems=FakeEcosystems({})
        )

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
        candidates.enrich(candidate, client=client, ecosystems=FakeEcosystems({}))
        candidate.refresh_from_db()
        assert candidate.depends_on_django is False

    def test_no_data_yet_is_unknown_not_false(self):
        assert baker.make(Candidate, pypi_data={}).depends_on_django is None

    def test_a_404_stores_no_data_but_stamps_the_attempt(self):
        candidate = baker.make(Candidate, name="gone", pypi_data={})
        assert not candidates.enrich(
            candidate, client=FakePyPI({}), ecosystems=FakeEcosystems({})
        )
        candidate.refresh_from_db()
        assert candidate.pypi_data == {}
        assert candidate.pypi_fetched_at is not None

    def test_enrich_missing_only_touches_rows_without_data(self):
        baker.make(Candidate, name="a", pypi_data={}, last_upload=WHEN)
        baker.make(Candidate, name="b", pypi_data={"info": {}}, last_upload=WHEN)
        baker.make(Candidate, name="c", pypi_data={}, last_upload=WHEN)
        client = FakePyPI({"a": pypi_json("a"), "c": pypi_json("c")})

        assert (
            candidates.enrich_missing(client=client, ecosystems=FakeEcosystems({})).pypi
            == 2
        )
        assert sorted(client.calls) == ["a", "c"]

    def test_enrich_missing_can_be_capped(self):
        for name in "abc":
            baker.make(Candidate, name=name, pypi_data={}, last_upload=WHEN)
        client = FakePyPI({n: pypi_json(n) for n in "abc"})
        assert (
            candidates.enrich_missing(
                limit=2, client=client, ecosystems=FakeEcosystems({})
            ).pypi
            == 2
        )


class TestEcosystems:
    def test_it_stores_the_trimmed_record_and_the_signals_read_off_it(self):
        candidate = baker.make(Candidate, name="openoutreach", pypi_data={})
        candidates.enrich(
            candidate,
            client=FakePyPI({"openoutreach": pypi_json("openoutreach")}),
            ecosystems=FakeEcosystems({"openoutreach": ECOSYSTEMS}),
        )
        candidate.refresh_from_db()
        assert candidate.stars == 3528
        assert candidate.repo_created == "2016-10-07"
        assert candidate.downloads == 2247
        assert candidate.dependents == 3
        assert candidate.advisories == 0
        assert candidate.ecosystems_data["repo"]["total_commits"] == 900
        assert "etag" not in candidate.ecosystems_data["repo"]
        assert "rankings" not in candidate.ecosystems_data
        assert candidate.ecosystems_data["maintainers"] == [
            {"login": "eracle", "packages_count": 2, "html_url": "x"}
        ]
        assert candidate.ecosystems_fetched_at is not None

    def test_its_repository_fills_in_when_pypi_has_none(self):
        candidate = baker.make(Candidate, name="build-wagtail", pypi_data={})
        candidates.enrich(
            candidate,
            client=FakePyPI(
                {"build-wagtail": pypi_json("build-wagtail", project_urls={})}
            ),
            ecosystems=FakeEcosystems({"build-wagtail": ECOSYSTEMS}),
        )
        candidate.refresh_from_db()
        assert candidate.repo_url == "https://github.com/eracle/OpenOutreach"

    def test_pypi_wins_when_both_name_a_repository(self):
        candidate = baker.make(Candidate, name="openoutreach", pypi_data={})
        candidates.enrich(
            candidate,
            client=FakePyPI({"openoutreach": pypi_json("openoutreach")}),
            ecosystems=FakeEcosystems({"openoutreach": ECOSYSTEMS}),
        )
        candidate.refresh_from_db()
        assert candidate.repo_url == "https://github.com/eracle/openoutreach"

    def test_a_name_they_have_not_seen_is_remembered_and_retried(self):
        candidate = baker.make(
            Candidate, name="brand-new", pypi_data={}, last_upload=WHEN
        )
        candidates.enrich(
            candidate,
            client=FakePyPI({"brand-new": pypi_json("brand-new")}),
            ecosystems=FakeEcosystems({}),
        )
        candidate.refresh_from_db()
        assert candidate.ecosystems_data == {}
        assert candidate.ecosystems_fetched_at is not None
        assert candidate.stars is None

        later = FakeEcosystems({"brand-new": ECOSYSTEMS})
        candidates.enrich_missing(client=FakePyPI({}), ecosystems=later)
        assert later.calls == ["brand-new"]
        candidate.refresh_from_db()
        assert candidate.stars == 3528

    def test_rejected_rows_are_not_retried(self):
        baker.make(
            Candidate,
            name="spam",
            pypi_data={"info": {}},
            status=Candidate.Status.REJECTED,
            last_upload=WHEN,
        )
        eco = FakeEcosystems({"spam": ECOSYSTEMS})
        candidates.enrich_missing(client=FakePyPI({}), ecosystems=eco)
        assert eco.calls == []

    def test_an_outage_there_does_not_block_the_pypi_half(self):
        candidate = baker.make(Candidate, name="openoutreach", pypi_data={})
        assert candidates.enrich(
            candidate,
            client=FakePyPI({"openoutreach": pypi_json("openoutreach")}),
            ecosystems=FakeEcosystems({}, fail=True),
        )
        candidate.refresh_from_db()
        assert candidate.author == "OpenOutreach"
        assert candidate.ecosystems_fetched_at is None

    def test_enrich_missing_asks_ecosystems_in_batches_of_100(self):
        for n in range(250):
            baker.make(Candidate, name=f"pkg-{n:03}", pypi_data={"info": {}})
        eco = FakeEcosystems({"pkg-007": ECOSYSTEMS})

        result = candidates.enrich_missing(client=FakePyPI({}), ecosystems=eco)

        assert [len(batch) for batch in eco.batches] == [100, 100, 50]
        assert (result.ecosystems_asked, result.ecosystems_found) == (250, 1)
        assert result.ecosystems_requests == 3
        assert Candidate.objects.filter(ecosystems_fetched_at__isnull=True).count() == 0
        assert Candidate.objects.get(name="pkg-007").stars == 3528

    def test_new_pypi_rows_are_asked_about_in_the_same_run(self):
        baker.make(Candidate, name="openoutreach", pypi_data={}, last_upload=WHEN)
        eco = FakeEcosystems({"openoutreach": ECOSYSTEMS})

        candidates.enrich_missing(
            client=FakePyPI({"openoutreach": pypi_json("openoutreach")}),
            ecosystems=eco,
        )

        assert eco.batches == [["openoutreach"]]
        assert Candidate.objects.get().stars == 3528

    def test_the_ecosystems_cap_counts_names(self):
        for n in range(30):
            baker.make(Candidate, name=f"pkg-{n:02}", pypi_data={"info": {}})
        eco = FakeEcosystems({})

        result = candidates.enrich_missing(
            client=FakePyPI({}), ecosystems=eco, ecosystems_limit=12
        )

        assert result.ecosystems_asked == 12

    def test_it_stops_when_their_quota_runs_low(self):
        for n in range(150):
            baker.make(Candidate, name=f"pkg-{n:03}", pypi_data={"info": {}})
        eco = FakeEcosystems({}, remaining=candidates.ECOSYSTEMS_RESERVE - 1)

        result = candidates.enrich_missing(client=FakePyPI({}), ecosystems=eco)

        assert eco.batches == []
        assert result.stopped_early

    def test_an_outage_leaves_the_rows_to_ask_again(self):
        baker.make(Candidate, name="a", pypi_data={"info": {}})
        eco = FakeEcosystems({}, fail=True)

        result = candidates.enrich_missing(client=FakePyPI({}), ecosystems=eco)

        assert result.stopped_early
        assert Candidate.objects.get().ecosystems_fetched_at is None

    def test_the_contact_email_goes_in_the_from_header_when_set(self, settings):
        from probes.ecosystems import EcosystemsClient

        settings.ECOSYSTEMS_CONTACT_EMAIL = "team@example.org"
        assert EcosystemsClient()._session.headers["From"] == "team@example.org"
        settings.ECOSYSTEMS_CONTACT_EMAIL = ""
        assert "From" not in EcosystemsClient()._session.headers


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
            patch(
                "probes.candidates.enrich_missing", return_value=candidates.Enriched()
            ) as enrich,
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


class TestFrameworkFilter:
    def filtered(self, value):
        params = {} if value is None else {"framework": value}
        request = RequestFactory().get("/", params)
        model_admin = CandidateAdmin(Candidate, AdminSite())
        lists = {key: [value] for key, value in params.items()}
        found = FrameworkFilter(request, lists, Candidate, model_admin)
        return set(
            found.queryset(request, Candidate.objects.all()).values_list(
                "name", flat=True
            )
        )

    def test_it_reads_the_classifiers(self):
        baker.make(Candidate, name="plain", classifiers=["Framework :: Django"])
        baker.make(
            Candidate,
            name="tail",
            classifiers=["Framework :: Django", "Framework :: Wagtail :: 7"],
        )
        baker.make(
            Candidate, name="cms", classifiers=["Framework :: Django CMS :: 4.1"]
        )
        baker.make(Candidate, name="bare", classifiers=[])

        assert self.filtered("wagtail") == {"tail"}
        assert self.filtered("django-cms") == {"cms"}
        assert self.filtered("django") == {"plain", "tail", "cms"}
        assert self.filtered(None) == {"plain", "tail", "cms", "bare"}


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


class FakeResponse:
    def __init__(self, payload, remaining="4321", status_code=200):
        self.payload = payload
        self.headers = {"x-ratelimit-remaining": remaining}
        self.status_code = status_code

    def json(self):
        return self.payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise httpx2.HTTPStatusError("boom", request=Mock(), response=self)


class TestBulkClient:
    def client(self, payload):
        from probes.ecosystems import EcosystemsClient

        client = EcosystemsClient(contact_email="")
        client._session = Mock()
        client._session.post.return_value = FakeResponse(payload)
        return client

    def test_it_matches_records_by_canonical_name(self):
        client = self.client(
            [
                {
                    **ECOSYSTEMS,
                    "name": "general-manager",
                    "registry": {"name": "pypi.org"},
                },
                {**ECOSYSTEMS, "name": "django-x", "registry": {"name": "npmjs.org"}},
            ]
        )

        found = client.fetch_packages(["General_Manager", "django-x"])

        assert list(found) == ["general-manager"]
        sent = client._session.post.call_args.kwargs["json"]["purls"]
        assert sent == ["pkg:pypi/django-x", "pkg:pypi/general-manager"]
        assert (client.requests, client.remaining) == (1, 4321)

    def test_bulk_requests_get_the_longer_timeout(self):
        from probes.ecosystems import BULK_TIMEOUT

        client = self.client([])
        client.fetch_packages(["django-x"])

        assert client._session.post.call_args.kwargs["timeout"] == BULK_TIMEOUT
        assert BULK_TIMEOUT > 10

    def test_more_than_100_names_is_refused(self):
        client = self.client([])
        with pytest.raises(ValueError):
            client.fetch_packages(f"pkg-{n}" for n in range(101))
        client._session.post.assert_not_called()
