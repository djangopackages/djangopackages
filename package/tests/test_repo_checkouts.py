"""Checkouts and the AST scan. Nothing here touches the network."""

import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest
from model_bakery import baker

from package.repo_checkouts import (
    CheckoutError,
    checkout_path,
    is_cloneable,
    iter_python_files,
    scan_checkout,
    sync_checkout,
)


class TestCloneable:
    @pytest.mark.parametrize(
        "url",
        [
            "https://github.com/djangopackages/djangopackages",
            "https://gitlab.com/group/project",
            "https://bitbucket.org/team/repo",
            "https://codeberg.org/user/repo",
        ],
    )
    def test_hosts_we_can_clone_from(self, url):
        assert is_cloneable(url)

    @pytest.mark.parametrize(
        "url",
        [
            "https://code.google.com/p/old",  # dead for a decade
            "https://pypi.org/project/thing/",  # not a repo at all
            "https://launchpad.net/thing",
            "",
            None,
        ],
    )
    def test_hosts_we_skip(self, url):
        assert not is_cloneable(url)

    def test_www_is_ignored(self):
        assert is_cloneable("https://www.github.com/a/b")


@pytest.mark.django_db
class TestCheckoutPath:
    def test_one_directory_per_slug(self, settings, tmp_path):
        settings.PACKAGE_REPO_ROOT = tmp_path
        package = baker.make("package.Package", slug="django-thing")

        assert checkout_path(package) == tmp_path / "django-thing"


@pytest.mark.django_db
class TestSyncCheckout:
    @pytest.fixture()
    def package(self, settings, tmp_path):
        settings.PACKAGE_REPO_ROOT = tmp_path
        return baker.make(
            "package.Package",
            slug="thing",
            repo_url="https://github.com/example/thing",
        )

    def test_an_uncloneable_url_is_refused_before_running_git(self, package):
        package.repo_url = "https://code.google.com/p/thing"

        with patch("package.repo_checkouts.subprocess.run") as run:
            with pytest.raises(CheckoutError, match="cannot clone"):
                sync_checkout(package)

        run.assert_not_called()

    def test_a_fresh_package_is_cloned(self, package):
        with patch("package.repo_checkouts.subprocess.run") as run:
            run.return_value = subprocess.CompletedProcess([], 0, "", "")

            _, action = sync_checkout(package)

        assert action == "cloned"
        assert run.call_args_list[0].args[0][:2] == ["git", "clone"]

    def test_an_existing_checkout_is_updated_not_recloned(self, package, tmp_path):
        (tmp_path / "thing" / ".git").mkdir(parents=True)

        with patch("package.repo_checkouts.subprocess.run") as run:
            run.return_value = subprocess.CompletedProcess([], 0, "abc123\n", "")

            _, action = sync_checkout(package)

        assert action == "updated"
        commands = [c.args[0][1] for c in run.call_args_list]
        assert "clone" not in commands
        assert commands[0] == "fetch"

    def test_git_is_never_allowed_to_prompt(self, package):
        """A private repo must fail fast, not block on a credential prompt."""
        with patch("package.repo_checkouts.subprocess.run") as run:
            run.return_value = subprocess.CompletedProcess([], 0, "", "")

            sync_checkout(package)

        assert run.call_args.kwargs["env"]["GIT_TERMINAL_PROMPT"] == "0"

    def test_a_failing_git_reports_its_last_line(self, package):
        with patch("package.repo_checkouts.subprocess.run") as run:
            run.return_value = subprocess.CompletedProcess(
                [], 128, "", "cloning into...\nfatal: repository not found"
            )

            with pytest.raises(CheckoutError, match="repository not found"):
                sync_checkout(package)

    def test_a_missing_git_binary_says_so(self, package):
        with patch("package.repo_checkouts.subprocess.run", side_effect=FileNotFoundError):
            with pytest.raises(CheckoutError, match="git is not installed"):
                sync_checkout(package)

    def test_a_hung_git_is_given_up_on(self, package):
        with patch(
            "package.repo_checkouts.subprocess.run",
            side_effect=subprocess.TimeoutExpired("git", 300),
        ):
            with pytest.raises(CheckoutError, match="timed out"):
                sync_checkout(package)


class TestIterPythonFiles:
    def test_vendored_and_build_directories_are_skipped(self, tmp_path):
        (tmp_path / "app").mkdir()
        (tmp_path / "app" / "models.py").write_text("")
        for junk in (".git", "node_modules", ".venv", "build"):
            (tmp_path / junk).mkdir()
            (tmp_path / junk / "noise.py").write_text("")

        found = {p.name for p in iter_python_files(tmp_path)}

        assert found == {"models.py"}


class TestScanCheckout:
    def test_it_resolves_imports_rather_than_matching_text(self, tmp_path):
        """`from django.db import models` then `models.CharField`."""
        (tmp_path / "models.py").write_text(
            "from django.db import models\n"
            "class Thing(models.Model):\n"
            "    name = models.CharField(max_length=10)\n"
        )

        result = scan_checkout(tmp_path)

        assert result.usage["django.db.models.Model"] == 1
        assert result.usage["django.db.models.CharField"] == 1
        assert result.files_scanned == 1

    def test_a_mention_in_a_string_is_not_a_use(self, tmp_path):
        (tmp_path / "noise.py").write_text('x = "django.db.models.CharField"\n')

        assert scan_checkout(tmp_path).usage == {}

    def test_an_unparseable_file_is_skipped_not_fatal(self, tmp_path):
        """Other people's repos contain Python 2 and worse."""
        (tmp_path / "bad.py").write_text("print 'py2'\n")
        (tmp_path / "good.py").write_text("from django.conf import settings\n")

        result = scan_checkout(tmp_path)

        assert result.files_skipped == 1
        assert result.files_scanned == 1
        assert "django.conf.settings" in result.usage

    def test_other_packages_can_be_counted_too(self, tmp_path):
        """The probe is not Django specific, which is the point."""
        (tmp_path / "views.py").write_text(
            "from rest_framework.views import APIView\n"
            "class V(APIView):\n    pass\n"
        )

        result = scan_checkout(tmp_path, ("django", "rest_framework"))

        assert result.usage["rest_framework.views.APIView"] == 2

    def test_an_empty_checkout_scans_to_nothing(self, tmp_path):
        result = scan_checkout(tmp_path)

        assert result.files_scanned == 0
        assert result.total == 0
