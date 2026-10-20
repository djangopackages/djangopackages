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
            "package.Package", slug="a", repo_url="https://github.com/x/a", score=1
        )

        with patch("package.repo_checkouts.subprocess.run") as run:
            call_command("sync_package_repos", "--dry-run")

        run.assert_not_called()

    def test_uncloneable_packages_are_skipped_not_attempted(self, repo_root):
        baker.make(
            "package.Package",
            slug="old",
            repo_url="https://code.google.com/p/old",
            score=1,
        )

        with patch("package.repo_checkouts.subprocess.run") as run:
            call_command("sync_package_repos")

        run.assert_not_called()

    def test_one_failure_does_not_stop_the_rest(self, repo_root):
        """A deleted repo is normal at this scale."""
        baker.make(
            "package.Package", slug="a", repo_url="https://github.com/x/a", score=2
        )
        baker.make(
            "package.Package", slug="b", repo_url="https://github.com/x/b", score=1
        )

        calls = []

        def fake(args, **kwargs):
            calls.append(args)
            if "a" in args[-1]:
                return subprocess.CompletedProcess([], 128, "", "fatal: not found")
            return subprocess.CompletedProcess([], 0, "", "")

        with patch("package.repo_checkouts.subprocess.run", side_effect=fake):
            call_command("sync_package_repos")

        assert any("/b" in str(c[-1]) for c in calls)

    def test_missing_only_leaves_existing_checkouts_alone(self, repo_root):
        baker.make(
            "package.Package", slug="a", repo_url="https://github.com/x/a", score=1
        )
        (repo_root / "a" / ".git").mkdir(parents=True)

        with patch("package.repo_checkouts.subprocess.run") as run:
            call_command("sync_package_repos", "--missing-only")

        run.assert_not_called()


class TestScanCommand:
    def test_a_package_with_no_checkout_is_counted_missing(self, repo_root, capsys):
        baker.make(
            "package.Package", slug="a", repo_url="https://github.com/x/a", score=1
        )

        call_command("scan_package_repos")

        assert "missing checkout 1" in capsys.readouterr().out

    def test_it_reports_what_a_checkout_uses(self, repo_root, capsys):
        baker.make(
            "package.Package", slug="a", repo_url="https://github.com/x/a", score=1
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
            "package.Package", slug="a", repo_url="https://github.com/x/a", score=1
        )
        (repo_root / "a" / ".git").mkdir(parents=True)

        with patch("package.repo_checkouts.subprocess.run") as run:
            call_command("scan_package_repos")

        run.assert_not_called()
