"""The two management commands, with git stubbed out."""

import subprocess
from unittest.mock import patch

import pytest
from django.core.management import call_command
from model_bakery import baker

pytestmark = pytest.mark.django_db


@pytest.fixture()
def repo_root(settings, tmp_path):
    settings.PACKAGE_REPO_ROOT = tmp_path
    return tmp_path


class TestSyncCommand:
    def test_a_dry_run_runs_no_git(self, repo_root):
        baker.make(
            "package.Package",
            slug="a",
            repo_url="https://github.com/x/a",
            pypi_url="https://pypi.org/project/a/",
            score=1,
        )

        with patch("probes.checkouts.subprocess.run") as run:
            call_command("sync_package_repos", "--dry-run")

        run.assert_not_called()

    def test_uncloneable_packages_are_skipped_not_attempted(self, repo_root):
        baker.make(
            "package.Package",
            slug="old",
            repo_url="https://code.google.com/p/old",
            score=1,
        )

        with patch("probes.checkouts.subprocess.run") as run:
            call_command("sync_package_repos")

        run.assert_not_called()

    def test_one_failure_does_not_stop_the_rest(self, repo_root):
        """A deleted repo is normal at this scale."""
        baker.make(
            "package.Package",
            slug="a",
            repo_url="https://github.com/x/a",
            pypi_url="https://pypi.org/project/a/",
            score=2,
        )
        baker.make(
            "package.Package",
            slug="b",
            repo_url="https://github.com/x/b",
            pypi_url="https://pypi.org/project/b/",
            score=1,
        )

        calls = []

        def fake(args, **kwargs):
            calls.append(args)
            if "a" in args[-1]:
                return subprocess.CompletedProcess([], 128, "", "fatal: not found")
            return subprocess.CompletedProcess([], 0, "", "")

        with patch("probes.checkouts.subprocess.run", side_effect=fake):
            call_command("sync_package_repos")

        assert any("/b" in str(c[-1]) for c in calls)

    def test_missing_only_leaves_existing_checkouts_alone(self, repo_root):
        baker.make(
            "package.Package",
            slug="a",
            repo_url="https://github.com/x/a",
            pypi_url="https://pypi.org/project/a/",
            score=1,
        )
        (repo_root / "a" / ".git").mkdir(parents=True)

        with patch("probes.checkouts.subprocess.run") as run:
            call_command("sync_package_repos", "--missing-only")

        run.assert_not_called()


class TestScanCommand:
    def test_a_package_with_no_checkout_is_counted_missing(self, repo_root, capsys):
        baker.make(
            "package.Package",
            slug="a",
            repo_url="https://github.com/x/a",
            pypi_url="https://pypi.org/project/a/",
            score=1,
        )

        call_command("scan_package_repos")

        assert "missing checkout 1" in capsys.readouterr().out

    def test_it_reports_what_a_checkout_uses(self, repo_root, capsys):
        baker.make(
            "package.Package",
            slug="a",
            repo_url="https://github.com/x/a",
            pypi_url="https://pypi.org/project/a/",
            score=1,
        )
        (repo_root / "a" / ".git").mkdir(parents=True)
        (repo_root / "a" / "models.py").write_text(
            "from django.db import models\nx = models.CharField\n"
        )

        call_command("scan_package_repos")

        out = capsys.readouterr().out
        assert "django.db.models.CharField" in out
        assert "scanned 1" in out

    def test_it_never_reaches_the_network(self, repo_root):
        """Scanning reads checkouts only; fetching is the other command."""
        baker.make(
            "package.Package",
            slug="a",
            repo_url="https://github.com/x/a",
            pypi_url="https://pypi.org/project/a/",
            score=1,
        )
        (repo_root / "a" / ".git").mkdir(parents=True)

        with patch("probes.checkouts.subprocess.run") as run:
            call_command("scan_package_repos")

        run.assert_not_called()


class TestWhichPackagesAreSynced:
    """The default set is "has a repo we can clone and a PyPI release"."""

    def test_a_package_with_no_pypi_release_is_left_out(self, repo_root, capsys):
        baker.make(
            "package.Package",
            slug="no-release",
            repo_url="https://github.com/x/no-release",
            pypi_url="",
            score=1,
        )

        call_command("sync_package_repos", "--dry-run")

        assert "no-release" not in capsys.readouterr().out

    def test_an_explicit_slug_still_reaches_it(self, repo_root, capsys):
        baker.make(
            "package.Package",
            slug="no-release",
            repo_url="https://github.com/x/no-release",
            pypi_url="",
            score=1,
        )

        call_command("sync_package_repos", "--slug", "no-release", "--dry-run")

        assert "no-release" in capsys.readouterr().out

    def test_an_unreachable_host_is_left_out(self, repo_root, capsys):
        baker.make(
            "package.Package",
            slug="googlecode",
            repo_url="https://code.google.com/p/old",
            pypi_url="https://pypi.org/project/googlecode/",
            score=1,
        )

        call_command("sync_package_repos", "--dry-run")

        assert "googlecode" not in capsys.readouterr().out

    def test_an_abandoned_package_is_left_out_by_default(self, repo_root, capsys):
        """Below zero means ~30 months untouched, not merely unpopular."""
        baker.make(
            "package.Package",
            slug="abandoned",
            repo_url="https://github.com/x/abandoned",
            pypi_url="https://pypi.org/project/abandoned/",
            score=-120,
        )

        call_command("sync_package_repos", "--dry-run")

        assert "abandoned" not in capsys.readouterr().out

    def test_min_score_can_reach_the_abandoned_ones(self, repo_root, capsys):
        baker.make(
            "package.Package",
            slug="abandoned",
            repo_url="https://github.com/x/abandoned",
            pypi_url="https://pypi.org/project/abandoned/",
            score=-120,
        )

        call_command("sync_package_repos", "--dry-run", "--min-score", "-500")

        assert "abandoned" in capsys.readouterr().out

    def test_a_brand_new_package_scoring_zero_is_kept(self, repo_root, capsys):
        """No stars yet is not the same as abandoned."""
        baker.make(
            "package.Package",
            slug="brand-new",
            repo_url="https://github.com/x/brand-new",
            pypi_url="https://pypi.org/project/brand-new/",
            score=0,
        )

        call_command("sync_package_repos", "--dry-run")

        assert "brand-new" in capsys.readouterr().out
