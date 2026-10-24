"""Dependents from deps.dev."""

from unittest.mock import patch

import httpx2
import pytest
from django.core.management import call_command
from model_bakery import baker

from package import deps_dev
from package.models import Package

pytestmark = pytest.mark.django_db

PACKAGE_JSON = {
    "packageKey": {"system": "PYPI", "name": "django-debug-toolbar"},
    "versions": [
        {"versionKey": {"version": "7.0.0"}, "isDefault": False},
        {"versionKey": {"version": "8.0.0"}, "isDefault": True},
    ],
}
DEPENDENTS_JSON = {
    "dependentCount": 90,
    "directDependentCount": 65,
    "indirectDependentCount": 25,
}


class FakeClient:
    """Answers by URL, so a test can script deps.dev."""

    def __init__(self, answers):
        self.answers = answers
        self.calls = []

    def get(self, url, timeout=None):
        self.calls.append(url)
        answer = self.answers.get(url)
        if isinstance(answer, Exception):
            raise answer
        if answer is None:
            return httpx2.Response(404, request=httpx2.Request("GET", url))
        if isinstance(answer, int):
            return httpx2.Response(answer, request=httpx2.Request("GET", url))
        return httpx2.Response(200, json=answer, request=httpx2.Request("GET", url))

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        pass


def _answers(name="django-debug-toolbar", version="8.0.0", **over):
    answers = {
        deps_dev.PACKAGE_URL.format(name=name): PACKAGE_JSON,
        deps_dev.DEPENDENTS_URL.format(name=name, version=version): DEPENDENTS_JSON,
    }
    answers.update(over)
    return answers


def _package(slug, pypi_name=None):
    return baker.make(
        Package,
        slug=slug,
        repo_url=f"https://github.com/x/{slug}",
        pypi_url=f"https://pypi.org/project/{pypi_name or slug}/",
    )


class TestFetch:
    def test_reads_the_default_version_then_its_dependents(self):
        client = FakeClient(_answers())

        found = deps_dev.fetch("Django_Debug_Toolbar", client=client)

        assert found == deps_dev.Dependents("8.0.0", 90, 65)
        # Spelling normalised in the URLs, PEP 503 style.
        assert all("django-debug-toolbar" in url for url in client.calls)

    def test_unknown_package_is_none(self):
        client = FakeClient({})

        assert deps_dev.fetch("nope", client=client) is None

    def test_a_server_error_is_retried_once_then_given_up(self):
        url = deps_dev.PACKAGE_URL.format(name="django-debug-toolbar")
        client = FakeClient({url: 503})

        with patch("package.deps_dev.time.sleep"), pytest.raises(deps_dev.NoAnswer):
            deps_dev.fetch("django-debug-toolbar", client=client)

        assert client.calls == [url, url]

    def test_a_dropped_connection_is_no_answer(self):
        url = deps_dev.PACKAGE_URL.format(name="django-debug-toolbar")
        client = FakeClient({url: httpx2.ConnectError("down")})

        with patch("package.deps_dev.time.sleep"), pytest.raises(deps_dev.NoAnswer):
            deps_dev.fetch("django-debug-toolbar", client=client)


class TestSync:
    def _run(self, answers, packages, **kwargs):
        client = FakeClient(answers)
        with (
            patch("package.deps_dev.httpx2.Client", return_value=client),
            patch("package.deps_dev.time.sleep"),
        ):
            return deps_dev.sync(packages, **kwargs), client

    def test_writes_dependents_onto_the_package(self):
        toolbar = _package("django-debug-toolbar")

        outcome, _client = self._run(_answers(), [toolbar])

        assert (outcome.asked, outcome.found) == (1, 1)
        toolbar.refresh_from_db()
        assert toolbar.pypi_dependents == 90
        assert toolbar.pypi_direct_dependents == 65
        assert toolbar.pypi_dependents_synced_at is not None

    def test_a_package_deps_dev_does_not_know_is_cleared(self):
        gone = _package("django-gone")
        Package.objects.filter(pk=gone.pk).update(pypi_dependents=12)

        outcome, _client = self._run({}, [gone])

        assert outcome.missing == 1
        gone.refresh_from_db()
        assert gone.pypi_dependents is None
        assert gone.pypi_dependents_synced_at is not None

    def test_no_answer_leaves_the_old_number(self):
        toolbar = _package("django-debug-toolbar")
        Package.objects.filter(pk=toolbar.pk).update(pypi_dependents=12)
        url = deps_dev.PACKAGE_URL.format(name="django-debug-toolbar")

        outcome, _client = self._run({url: 503}, [toolbar])

        assert outcome.no_answer == 1
        toolbar.refresh_from_db()
        assert toolbar.pypi_dependents == 12
        assert toolbar.pypi_dependents_synced_at is None

    def test_packages_without_a_pypi_name_are_skipped(self):
        bare = baker.make(
            Package, slug="bare", repo_url="https://github.com/x/bare", pypi_url=""
        )

        outcome, client = self._run({}, [bare])

        assert outcome.asked == 0
        assert client.calls == []

    def test_dry_run_saves_nothing(self):
        toolbar = _package("django-debug-toolbar")

        outcome, _client = self._run(_answers(), [toolbar], save=False)

        assert outcome.found == 1
        toolbar.refresh_from_db()
        assert toolbar.pypi_dependents is None


class TestCommand:
    def test_syncs_the_named_package(self, capsys):
        toolbar = _package("django-debug-toolbar")
        _package("django-other")
        client = FakeClient(_answers())

        with (
            patch("package.deps_dev.httpx2.Client", return_value=client),
            patch("package.deps_dev.time.sleep"),
        ):
            call_command("deps_dev_sync", "--slug", "django-debug-toolbar")

        toolbar.refresh_from_db()
        assert toolbar.pypi_dependents == 90
        assert "1 on deps.dev" in capsys.readouterr().out

    def test_the_job_is_scheduled(self):
        from core.management.commands.init_scheduled_jobs import JOBS

        assert JOBS["deps-dev"]["args"] == ("deps_dev_sync",)


class TestPackagePage:
    def test_dependents_show_once_synced(self, client):
        package = _package("django-debug-toolbar")
        Package.objects.filter(pk=package.pk).update(pypi_dependents=1234)

        response = client.get(package.get_absolute_url())

        assert b"1,234" in response.content
        assert b"per deps.dev" in response.content

    def test_nothing_shows_before_the_first_sync(self, client):
        package = _package("django-debug-toolbar")

        response = client.get(package.get_absolute_url())

        assert b"per deps.dev" not in response.content
