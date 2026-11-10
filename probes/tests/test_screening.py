from __future__ import annotations

from datetime import UTC, datetime, timedelta
from unittest.mock import Mock

import httpx2
import pytest
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import RequestFactory
from model_bakery import baker

from probes import candidates, screening
from probes.admin import CandidateAdmin, ReasonFilter
from probes.models import Candidate

pytestmark = pytest.mark.django_db

NOW = datetime(2026, 11, 10, tzinfo=UTC)
OLD = datetime(2019, 3, 1, tzinfo=UTC)


def pypi(*, requires=("Django>=4.2",), releases=None, email="a@example.com"):
    return {
        "info": {"author_email": email, "requires_dist": list(requires)},
        "releases": releases or {"1.0": "2019-03-01T00:00:00Z"},
    }


def ecosystems(*, stars=12, downloads=900, dependents=2, **repo):
    return {
        "downloads": downloads,
        "dependent_repos_count": dependents,
        "advisories": 0,
        "repo": {
            "full_name": "someone/django-thing",
            "stargazers_count": stars,
            "fork": False,
            "created_at": "2019-02-01T00:00:00Z",
            **repo,
        },
    }


def healthy(name="django-thing", **fields):
    """A candidate no rule should fire on."""
    values = {
        "name": name,
        "summary": "Does a useful thing for Django sites",
        "first_upload": OLD,
        "last_upload": OLD,
        "repo_url": f"https://github.com/someone/{name}",
        "pypi_data": pypi(),
        "pypi_fetched_at": NOW,
        "ecosystems_data": ecosystems(full_name=f"someone/{name}"),
    }
    values.update(fields)
    return Candidate(**values)


def screen(candidate, *others):
    context = screening.Context.build([candidate, *others], now=NOW)
    return screening.screen(candidate, context)


def daily(count, start=datetime(2026, 9, 1, tzinfo=UTC), step=timedelta(days=1)):
    return {f"0.{i}": (start + step * i).isoformat() for i in range(count)}


class TestRules:
    def test_a_healthy_package_fires_nothing(self):
        assert screen(healthy()) == []

    def test_a_404_from_pypi_is_removed(self):
        reasons = screen(healthy(pypi_data={}, ecosystems_data={}))
        assert reasons == ["removed-from-pypi"]
        assert screening.should_hold(reasons)

    def test_never_fetched_is_not_removed(self):
        assert screen(healthy(pypi_data={}, pypi_fetched_at=None)) == []

    def test_a_misspelled_django_name(self):
        assert screen(healthy("djnago-file-explorer")) == ["misspelled-django"]

    def test_a_release_flood(self):
        flood = healthy(pypi_data=pypi(releases=daily(30)))
        steady = healthy(pypi_data=pypi(releases=daily(30, step=timedelta(days=40))))
        assert screen(flood) == ["release-flood"]
        assert screen(steady) == []

    def test_no_framework_in_requires_dist(self):
        candidate = healthy(pypi_data=pypi(requires=("httpx",)))
        assert screen(candidate) == ["no-framework-dependency"]

    def test_repository_signals(self):
        assert screen(healthy(repo_url="")) == ["no-repository"]
        assert screen(healthy(ecosystems_data={**ecosystems(), "repo": {}})) == [
            "repository-unknown"
        ]
        forked = healthy(ecosystems_data=ecosystems(fork=True))
        assert screen(forked) == ["repository-fork"]
        unrelated = healthy(ecosystems_data=ecosystems(full_name="x/MCP-Watch"))
        assert screen(unrelated) == ["repository-unrelated"]

    def test_no_traction(self):
        quiet = healthy(ecosystems_data=ecosystems(stars=0, downloads=3, dependents=0))
        assert screen(quiet) == ["no-traction"]

    def test_placeholder_summaries(self):
        assert screen(healthy(summary="Add your description here")) == [
            "placeholder-summary"
        ]
        assert screen(healthy("tidy", summary="tidy")) == ["placeholder-summary"]

    def test_bursts_need_two_others(self):
        minute = datetime(2026, 11, 7, 18, 45, 3, tzinfo=UTC)
        rows = [
            healthy(f"karni-{n}", first_upload=minute + timedelta(seconds=n))
            for n in range(3)
        ]
        assert "upload-burst" in screen(rows[0], *rows[1:])
        assert "upload-burst" not in screen(rows[0], rows[1])

    def test_author_burst_only_counts_new_names(self):
        recent = pypi(releases={"0.1": "2026-10-20T00:00:00Z"}, email="b@x.io")
        rows = [
            healthy(
                f"suite-{n}", first_upload=NOW - timedelta(days=20), pypi_data=recent
            )
            for n in range(3)
        ]
        old = [healthy(f"old-{n}", pypi_data=pypi(email="b@x.io")) for n in range(3)]
        assert "author-burst" in screen(rows[0], *rows[1:])
        assert "author-burst" not in screen(old[0], *old[1:])


class TestHolding:
    def test_one_weak_reason_is_not_enough(self):
        assert not screening.should_hold(["no-repository"])

    def test_two_weak_reasons_hold(self):
        assert screening.should_hold(["no-repository", "no-traction"])

    def test_informational_reasons_never_count(self):
        assert not screening.should_hold(["no-traction", "brand-new"])
        assert not screening.should_hold(["brand-new", "repository-after-release"])


class TestScreenAll:
    def test_apply_holds_and_records_reasons(self):
        healthy().save()
        healthy("removed", pypi_data={}, ecosystems_data={}).save()

        result = screening.screen_all(apply=True)

        assert (result.seen, result.held, result.changed) == (2, 1, 1)
        removed = Candidate.objects.get(name="removed")
        assert removed.status == Candidate.Status.HELD
        assert removed.reasons == ["removed-from-pypi"]
        assert Candidate.objects.get(name="django-thing").status == Candidate.Status.NEW

    def test_a_dry_run_saves_nothing(self):
        healthy("removed", pypi_data={}, ecosystems_data={}).save()

        result = screening.screen_all(apply=False)

        assert result.held == 1
        assert Candidate.objects.get(name="removed").status == Candidate.Status.NEW

    def test_reviewed_and_decided_rows_are_left_alone(self):
        user = User.objects.create_user("reviewer")
        healthy(
            "kept", pypi_data={}, ecosystems_data={}, reviewed_by=user, status="new"
        ).save()
        healthy("gone", pypi_data={}, ecosystems_data={}, status="rejected").save()

        assert screening.screen_all(apply=True).seen == 0
        assert set(Candidate.objects.values_list("status", flat=True)) == {
            "new",
            "rejected",
        }

    def test_a_held_row_goes_back_to_new_when_it_clears(self):
        healthy(status=Candidate.Status.HELD, reasons=["no-repository"]).save()

        result = screening.screen_all(apply=True)

        assert result.released == 1
        saved = Candidate.objects.get()
        assert (saved.status, saved.reasons) == (Candidate.Status.NEW, [])

    def test_the_command_dry_runs_by_default(self):
        healthy("removed", pypi_data={}, ecosystems_data={}).save()

        call_command("screen_candidates")
        assert Candidate.objects.get().status == Candidate.Status.NEW

        call_command("screen_candidates", "--apply")
        assert Candidate.objects.get().status == Candidate.Status.HELD


class TestRemovedFromPyPI:
    def missing(self):
        client = Mock()
        response = Mock(status_code=404)
        client.fetch_package.side_effect = httpx2.HTTPStatusError(
            "404", request=Mock(), response=response
        )
        return client

    def test_a_404_is_stamped_and_not_asked_again(self):
        baker.make(Candidate, name="gone", last_upload=OLD, pypi_data={})
        client, eco = self.missing(), Mock()

        assert candidates.enrich_missing(client=client, ecosystems=eco).pypi == 0
        assert Candidate.objects.get().pypi_fetched_at is not None

        candidates.enrich_missing(client=client, ecosystems=eco)
        assert client.fetch_package.call_count == 1

    def test_a_newer_upload_is_asked_again(self):
        baker.make(
            Candidate,
            name="back",
            last_upload=NOW,
            pypi_fetched_at=NOW - timedelta(days=3),
            pypi_data={},
        )
        client = self.missing()

        candidates.enrich_missing(client=client, ecosystems=Mock())

        assert client.fetch_package.call_count == 1

    def test_a_server_error_is_not_a_removal(self):
        baker.make(Candidate, name="flaky", last_upload=OLD, pypi_data={})
        client = Mock()
        client.fetch_package.side_effect = httpx2.HTTPStatusError(
            "503", request=Mock(), response=Mock(status_code=503)
        )

        candidates.enrich_missing(client=client, ecosystems=Mock())

        assert Candidate.objects.get().pypi_fetched_at is None


class TestReasonFilter:
    def test_it_filters_by_one_reason(self):
        baker.make(Candidate, name="a", reasons=["no-repository", "no-traction"])
        baker.make(Candidate, name="b", reasons=["no-traction"])
        baker.make(Candidate, name="c", reasons=[])
        request = RequestFactory().get("/", {"reason": "no-traction"})
        model_admin = CandidateAdmin(Candidate, AdminSite())

        found = ReasonFilter(
            request, {"reason": ["no-traction"]}, Candidate, model_admin
        )

        names = found.queryset(request, Candidate.objects.all()).values_list(
            "name", flat=True
        )
        assert set(names) == {"a", "b"}
