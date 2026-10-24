"""The pipeline as Django Q tasks, with git and the network stubbed out."""

from datetime import timedelta
from unittest.mock import patch

import pytest
from django.core.management import call_command
from django.utils.timezone import now
from django_q.models import Schedule
from model_bakery import baker

from probes import tasks
from probes.models import Library, PackageProbe

pytestmark = pytest.mark.django_db


@pytest.fixture()
def repo_root(settings, tmp_path):
    settings.PACKAGE_REPO_ROOT = tmp_path
    return tmp_path


def make_package(slug, **kwargs):
    kwargs.setdefault("repo_url", f"https://github.com/x/{slug}")
    kwargs.setdefault("pypi_url", f"https://pypi.org/project/{slug}/")
    kwargs.setdefault("score", 1)
    return baker.make("package.Package", slug=slug, **kwargs)


class TestCheckPackageSource:
    def test_records_a_verdict(self):
        package = make_package("a")

        with (
            patch("probes.pipeline.repo_is_reachable", return_value=(True, "")),
            patch("probes.pipeline.pypi_is_published", return_value=(True, "")),
        ):
            assert tasks.check_package_source("a") == "on"

        package.refresh_from_db()
        assert package.probe is True
        assert package.probe_checked_at is not None

    def test_records_why_it_is_off(self):
        package = make_package("a")

        with patch(
            "probes.pipeline.repo_is_reachable",
            return_value=(False, "repo is private or deleted"),
        ):
            assert tasks.check_package_source("a").startswith("off:")

        package.refresh_from_db()
        assert package.probe is False
        assert package.probe_note == "repo is private or deleted"

    def test_no_answer_changes_nothing(self):
        package = make_package("a", probe=True)

        with patch(
            "probes.pipeline.repo_is_reachable", return_value=(None, "timed out")
        ):
            assert tasks.check_package_source("a").startswith("no answer")

        package.refresh_from_db()
        assert package.probe is True
        assert package.probe_checked_at is None


class TestRefreshPackageCheckout:
    def test_syncs_records_the_import_name_and_scans(self, repo_root):
        package = make_package("my-thing")
        path = repo_root / "my-thing"
        (path / ".git").mkdir(parents=True)
        (path / "my_thing").mkdir()
        (path / "my_thing" / "__init__.py").write_text("")
        (path / "my_thing" / "models.py").write_text(
            "from django.db import models\nx = models.CharField\n"
        )

        with (
            patch("probes.pipeline.sync_checkout", return_value=(path, "updated")),
            patch("probes.pipeline.checkout_commit", return_value="abc123"),
        ):
            assert tasks.refresh_package_checkout("my-thing") == "updated, scanned"

        package.refresh_from_db()
        assert package.probe_bytes > 0
        assert Library.objects.get(pypi_name="my-thing").import_name == "my_thing"
        profile = PackageProbe.objects.get(package=package)
        assert profile.commit == "abc123"
        assert {row["symbol"] for row in profile.symbols} >= {
            "django.db.models.CharField"
        }

    def test_a_failed_sync_stops_there(self, repo_root):
        from probes.checkouts import CheckoutError

        make_package("a")

        with (
            patch("probes.pipeline.sync_checkout", side_effect=CheckoutError("gone")),
            patch("probes.pipeline.scan_checkout") as scan,
        ):
            assert tasks.refresh_package_checkout("a") == "failed: gone"

        scan.assert_not_called()
        assert not PackageProbe.objects.exists()

    def test_an_unchanged_checkout_is_not_rescanned(self, repo_root):
        package = make_package("a")
        path = repo_root / "a"
        (path / ".git").mkdir(parents=True)
        PackageProbe.objects.create(
            package=package, commit="abc123", libraries=["django"], scanned_at=now()
        )

        with (
            patch("probes.pipeline.sync_checkout", return_value=(path, "updated")),
            patch("probes.pipeline.checkout_commit", return_value="abc123"),
            patch("probes.pipeline.scan_checkout") as scan,
        ):
            assert tasks.refresh_package_checkout("a") == "updated, unchanged"

        scan.assert_not_called()

    def test_an_uncloneable_repo_is_skipped_without_git(self, repo_root):
        make_package("old", repo_url="https://code.google.com/p/old")

        with patch("probes.checkouts.subprocess.run") as run:
            assert tasks.refresh_package_checkout("old").startswith("skipped")

        run.assert_not_called()

    def test_the_size_cap_discards_and_marks_the_package(self, repo_root):
        package = make_package("big")
        path = repo_root / "big"
        (path / ".git").mkdir(parents=True)

        with (
            patch("probes.pipeline.sync_checkout", return_value=(path, "cloned")),
            patch("probes.pipeline.checkout_size", return_value=5 * 1024 * 1024),
        ):
            result = tasks.refresh_package_checkout("big", max_mb=1)

        assert result.startswith("too_big")
        package.refresh_from_db()
        assert package.probe_wanted is False
        assert not path.exists()


class TestQueueProbeRefresh:
    def queued(self, async_task):
        return {(call.args[0], call.args[1]) for call in async_task.call_args_list}

    def test_checks_undecided_and_stale_packages_only(self):
        make_package("new")  # never looked at
        make_package("stale", probe=True, probe_checked_at=now() - timedelta(days=40))
        make_package("fresh", probe=True, probe_checked_at=now() - timedelta(days=2))
        make_package("off", probe=False, probe_checked_at=now() - timedelta(days=2))

        with patch("probes.tasks.async_task") as async_task:
            counts = tasks.queue_probe_refresh()

        checks = {
            slug
            for func, slug in self.queued(async_task)
            if func == "probes.tasks.check_package_source"
        }
        assert checks == {"new", "stale"}
        assert counts["checks"] == 2

    def test_refreshes_what_the_commands_would_sync(self):
        make_package("yes")
        make_package("off", probe=False)
        make_package("unwanted", probe_wanted=False)
        make_package("abandoned", score=-10)
        make_package("nowhere", repo_url="https://code.google.com/p/nowhere")

        with patch("probes.tasks.async_task") as async_task:
            counts = tasks.queue_probe_refresh()

        refreshes = {
            slug
            for func, slug in self.queued(async_task)
            if func == "probes.tasks.refresh_package_checkout"
        }
        assert refreshes == {"yes"}
        assert counts["refreshes"] == 1

    def test_refresh_tasks_get_a_long_enough_timeout(self):
        make_package("a")

        with patch("probes.tasks.async_task") as async_task:
            tasks.queue_probe_refresh()

        refresh = next(
            call
            for call in async_task.call_args_list
            if call.args[0] == "probes.tasks.refresh_package_checkout"
        )
        assert refresh.kwargs["q_options"]["timeout"] == tasks.REFRESH_TIMEOUT
        assert refresh.kwargs["q_options"]["group"] == "probe-refresh"

    def test_limit_caps_both_queues(self):
        for i in range(3):
            make_package(f"p{i}")

        with patch("probes.tasks.async_task"):
            counts = tasks.queue_probe_refresh(limit=2)

        assert counts == {"checks": 2, "refreshes": 2}


class TestInitScheduledJobs:
    def test_only_adds_the_jobs_asked_for(self):
        call_command("init_scheduled_jobs", "--only", "probe-refresh")

        assert list(Schedule.objects.values_list("func", flat=True)) == [
            "probes.tasks.queue_probe_refresh"
        ]

    def test_rerunning_does_not_duplicate(self):
        call_command("init_scheduled_jobs", "--only", "probe-catalog")
        call_command("init_scheduled_jobs", "--only", "probe-catalog")

        assert Schedule.objects.count() == 1

    def test_default_adds_everything(self):
        from core.management.commands.init_scheduled_jobs import JOBS

        call_command("init_scheduled_jobs")

        assert Schedule.objects.count() == len(JOBS)
