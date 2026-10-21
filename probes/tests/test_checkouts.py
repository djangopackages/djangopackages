"""Checkouts and the AST scan. Nothing here touches the network."""

import subprocess
import warnings
from unittest.mock import patch

import pytest
from model_bakery import baker

from probes.checkouts import (
    pypi_is_published,
    repo_is_reachable,
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

        with patch("probes.checkouts.subprocess.run") as run:
            with pytest.raises(CheckoutError, match="cannot clone"):
                sync_checkout(package)

        run.assert_not_called()

    def test_a_fresh_package_is_cloned(self, package):
        with patch("probes.checkouts.subprocess.run") as run:
            run.return_value = subprocess.CompletedProcess([], 0, "", "")

            _, action = sync_checkout(package)

        assert action == "cloned"
        assert run.call_args_list[0].args[0][:2] == ["git", "clone"]

    def test_an_existing_checkout_is_updated_not_recloned(self, package, tmp_path):
        (tmp_path / "thing" / ".git").mkdir(parents=True)

        with patch("probes.checkouts.subprocess.run") as run:
            run.return_value = subprocess.CompletedProcess([], 0, "abc123\n", "")

            _, action = sync_checkout(package)

        assert action == "updated"
        commands = [c.args[0][1] for c in run.call_args_list]
        assert "clone" not in commands
        assert commands[0] == "fetch"

    def test_git_is_never_allowed_to_prompt(self, package):
        """A private repo must fail fast, not block on a credential prompt."""
        with patch("probes.checkouts.subprocess.run") as run:
            run.return_value = subprocess.CompletedProcess([], 0, "", "")

            sync_checkout(package)

        assert run.call_args.kwargs["env"]["GIT_TERMINAL_PROMPT"] == "0"

    def test_a_failing_git_reports_its_last_line(self, package):
        with patch("probes.checkouts.subprocess.run") as run:
            run.return_value = subprocess.CompletedProcess(
                [], 128, "", "cloning into...\nfatal: repository not found"
            )

            with pytest.raises(CheckoutError, match="repository not found"):
                sync_checkout(package)

    def test_a_missing_git_binary_says_so(self, package):
        with patch("probes.checkouts.subprocess.run", side_effect=FileNotFoundError):
            with pytest.raises(CheckoutError, match="git is not installed"):
                sync_checkout(package)

    def test_a_hung_git_is_given_up_on(self, package):
        with patch(
            "probes.checkouts.subprocess.run",
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

    def test_egg_info_directories_are_skipped(self, tmp_path):
        """A built egg-info holds a copy of the source, which would
        double every count in it."""
        (tmp_path / "models.py").write_text("")
        egg = tmp_path / "thing.egg-info"
        egg.mkdir()
        (egg / "models.py").write_text("")

        found = [*iter_python_files(tmp_path)]

        assert [p.name for p in found] == ["models.py"]
        assert all("egg-info" not in str(p) for p in found)


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
            "from rest_framework.views import APIView\nclass V(APIView):\n    pass\n"
        )

        result = scan_checkout(tmp_path, ("django", "rest_framework"))

        assert result.usage["rest_framework.views.APIView"] == 2

    def test_an_empty_checkout_scans_to_nothing(self, tmp_path):
        result = scan_checkout(tmp_path)

        assert result.files_scanned == 0
        assert result.total == 0

    def test_a_file_that_opens_with_a_bom_is_still_read(self, tmp_path):
        """Decoded as text the BOM survives as U+FEFF and the parse
        fails, so the file silently went uncounted."""
        (tmp_path / "models.py").write_bytes(
            b"\xef\xbb\xbf" + b"from django.db import models\nx = models.CharField\n"
        )

        result = scan_checkout(tmp_path)

        assert result.files_skipped == 0
        assert result.usage["django.db.models.CharField"] == 1

    def test_a_declared_encoding_is_honoured(self, tmp_path):
        """A latin-1 file cannot be decoded as UTF-8, but the parser can
        read it from its own declaration."""
        (tmp_path / "old.py").write_bytes(
            "# -*- coding: latin-1 -*-\n"
            "from django.db import models\n"
            'AUTHOR = "Jos\u00e9"\n'
            "x = models.CharField\n".encode("latin-1")
        )

        result = scan_checkout(tmp_path)

        assert result.files_skipped == 0
        assert result.usage["django.db.models.CharField"] == 1

    def test_a_syntax_warning_is_not_raised_at_whoever_ran_the_scan(self, tmp_path):
        """An invalid escape sequence is normal in an old repo, and
        nobody running a scan over four thousand of them can act on it."""
        (tmp_path / "old.py").write_text('x = "\\d+"\ny = 1\n')

        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            result = scan_checkout(tmp_path)

        assert result.files_scanned == 1
        assert [w for w in caught if issubclass(w.category, SyntaxWarning)] == []


class TestScanCountsPatterns:
    """django-probe's named probes, which a dotted path cannot express."""

    def test_a_decorator_and_a_context_manager_both_count(self, tmp_path):
        (tmp_path / "views.py").write_text(
            "from django.db import transaction\n"
            "@transaction.atomic\n"
            "def one():\n"
            "    pass\n"
            "def two():\n"
            "    with transaction.atomic():\n"
            "        pass\n"
        )

        result = scan_checkout(tmp_path)

        assert result.patterns["probe:transaction_atomic"] == 2

    def test_queryset_calls_are_named_rather_than_counted_as_symbols(self, tmp_path):
        (tmp_path / "queries.py").write_text(
            "from django.db import models\n"
            "class Thing(models.Model):\n"
            "    pass\n"
            "rows = Thing.objects.filter(a=1).exclude(b=2)\n"
        )

        result = scan_checkout(tmp_path)

        assert result.patterns["probe:queryset_filter"] == 1
        assert result.patterns["probe:queryset_exclude"] == 1

    def test_a_checkout_with_no_patterns_reports_none(self, tmp_path):
        (tmp_path / "models.py").write_text("from django.db import models\n")

        assert scan_checkout(tmp_path).patterns == {}


class TestSettingsAreKeptDistinct:
    def test_a_known_setting_keeps_its_name(self, tmp_path):
        (tmp_path / "app.py").write_text(
            "from django.conf import settings\n"
            "a = settings.AUTH_USER_MODEL\n"
            "b = settings.DEBUG\n"
            "c = settings.DEBUG\n"
        )

        result = scan_checkout(tmp_path)

        assert result.usage["django.conf.settings.AUTH_USER_MODEL"] == 1
        assert result.usage["django.conf.settings.DEBUG"] == 2
        assert result.settings_used == {"AUTH_USER_MODEL": 1, "DEBUG": 2}

    def test_a_setting_django_does_not_define_folds_to_the_bare_path(self, tmp_path):
        """Every project invents its own settings, and listing them all
        would say more about naming habits than about Django."""
        (tmp_path / "app.py").write_text(
            "from django.conf import settings\nx = settings.MY_OWN_THING\n"
        )

        result = scan_checkout(tmp_path)

        # Two: the import, and the unrecognised setting folded onto it.
        assert result.usage["django.conf.settings"] == 2
        assert result.settings_used == {}


class TestReachabilityChecks:
    """The cheap pre-flight that decides `probe`, with git stubbed out."""

    def test_an_unclonable_host_never_touches_the_network(self):
        with patch("probes.checkouts.subprocess.run") as run:
            ok, note = repo_is_reachable("https://code.google.com/p/old")

        assert ok is False
        assert "cannot clone" in note
        run.assert_not_called()

    def test_it_asks_the_remote_without_cloning(self):
        with patch("probes.checkouts.subprocess.run") as run:
            run.return_value = subprocess.CompletedProcess([], 0, "sha\tHEAD\n", "")
            ok, note = repo_is_reachable("https://github.com/x/a")

        assert (ok, note) == (True, "")
        assert "ls-remote" in run.call_args[0][0]
        assert "clone" not in run.call_args[0][0]

    def test_a_credential_prompt_is_reported_as_gone(self):
        """GitHub asks for a username for both private and deleted repos."""
        with patch("probes.checkouts.subprocess.run") as run:
            run.return_value = subprocess.CompletedProcess(
                [], 128, "", "fatal: could not read Username for 'https://github.com'"
            )
            ok, note = repo_is_reachable("https://github.com/x/gone")

        assert ok is False
        assert note == "repo is private or deleted"

    def test_a_blank_pypi_url_is_not_published(self):
        assert pypi_is_published("") == (False, "no pypi url")
