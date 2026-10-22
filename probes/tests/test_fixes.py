"""Scanning untrusted repos safely, syncing, source checks, and the catalogue."""

import os
import subprocess
from unittest.mock import patch

import pytest
from django.core.cache import caches
from django.core.management import call_command
from django.utils.timezone import now
from model_bakery import baker

from probes import checkouts, django_docs, removals, stats
from probes.checkouts import (
    iter_python_files,
    pypi_is_published,
    repo_is_reachable,
    scan_checkout,
    sync_checkout,
)
from probes.models import PackageProbe, ProbeSymbol


@pytest.fixture()
def repo_root(settings, tmp_path):
    settings.PACKAGE_REPO_ROOT = tmp_path
    return tmp_path


def make_package(slug="a", **kwargs):
    return baker.make(
        "package.Package",
        slug=slug,
        title=slug,
        repo_url=f"https://github.com/x/{slug}",
        pypi_url=f"https://pypi.org/project/{slug}/",
        score=1,
        **kwargs,
    )


class TestScanSurvivesBadFiles:
    def test_a_file_too_deep_to_parse_is_skipped(self, tmp_path):
        """The parser reports this with a MemoryError, not a SyntaxError."""
        (tmp_path / "deep.py").write_text("x = " + "-" * 200_000 + "1\n")
        (tmp_path / "fine.py").write_text("from django.db import models\n")

        result = scan_checkout(tmp_path)

        assert result.files_skipped == 1
        assert result.files_scanned == 1

    def test_a_visitor_that_recurses_too_far_skips_the_file(self, tmp_path):
        (tmp_path / "a.py").write_text("x = 1\n")

        with patch(
            "django_probe.usage.count_package_usage", side_effect=RecursionError
        ):
            result = scan_checkout(tmp_path)

        assert result.files_skipped == 1
        assert result.files_scanned == 0

    def test_a_huge_file_is_skipped_unread(self, tmp_path, monkeypatch):
        monkeypatch.setattr(checkouts, "MAX_FILE_BYTES", 10)
        (tmp_path / "generated.py").write_text("x = 1\n" * 10)

        result = scan_checkout(tmp_path)

        assert result.files_skipped == 1

    def test_symlinks_are_never_followed(self, tmp_path):
        outside = tmp_path / "outside.py"
        outside.write_text("from django.db import models\n")
        root = tmp_path / "repo"
        root.mkdir()
        (root / "real.py").write_text("")
        os.symlink(outside, root / "link.py")
        os.symlink("/dev/zero", root / "zero.py")

        assert [p.name for p in iter_python_files(root)] == ["real.py"]


@pytest.mark.django_db
class TestSyncCheckoutGit:
    @pytest.fixture()
    def package(self, repo_root):
        return make_package("thing")

    def test_an_update_fetches_head_not_the_branch_we_cloned(self, package, repo_root):
        """A repo that renames master to main must keep updating."""
        (repo_root / "thing" / ".git").mkdir(parents=True)

        with patch("probes.checkouts.subprocess.run") as run:
            run.return_value = subprocess.CompletedProcess([], 0, "abc\n", "")
            sync_checkout(package)

        fetch = run.call_args_list[0].args[0]
        assert fetch[:2] == ["git", "fetch"]
        assert fetch[-2:] == ["origin", "HEAD"]

    def test_depth_zero_clones_full_history(self, package):
        with patch("probes.checkouts.subprocess.run") as run:
            run.return_value = subprocess.CompletedProcess([], 0, "", "")
            sync_checkout(package, depth=0)

        clone = run.call_args_list[0].args[0]
        assert "--depth" not in clone

    def test_depth_zero_fetches_without_a_depth(self, package, repo_root):
        (repo_root / "thing" / ".git").mkdir(parents=True)

        with patch("probes.checkouts.subprocess.run") as run:
            run.return_value = subprocess.CompletedProcess([], 0, "abc\n", "")
            sync_checkout(package, depth=0)

        assert "--depth" not in run.call_args_list[0].args[0]

    def test_a_dry_run_stops_at_the_limit(self, repo_root, capsys):
        for slug in ("a", "b", "c"):
            make_package(slug)

        call_command("sync_package_repos", "--dry-run", "--limit", "2")

        assert capsys.readouterr().out.count("would clone") == 2


class TestTransientFailures:
    def test_a_timeout_is_no_answer(self):
        with patch(
            "probes.checkouts.subprocess.run",
            side_effect=subprocess.TimeoutExpired("git", 30),
        ):
            ok, note = repo_is_reachable("https://github.com/x/a")

        assert ok is None
        assert "timed out" in note

    def test_a_dns_failure_is_no_answer(self):
        with patch("probes.checkouts.subprocess.run") as run:
            run.return_value = subprocess.CompletedProcess(
                [],
                128,
                "",
                "fatal: unable to access: Could not resolve host: github.com",
            )
            ok, _note = repo_is_reachable("https://github.com/x/a")

        assert ok is None

    def test_a_missing_repo_is_still_a_no(self):
        with patch("probes.checkouts.subprocess.run") as run:
            run.return_value = subprocess.CompletedProcess(
                [], 128, "", "fatal: repository 'x' not found"
            )
            ok, _note = repo_is_reachable("https://github.com/x/a")

        assert ok is False

    @pytest.mark.parametrize(
        ("status", "expected"),
        [(200, True), (404, False), (410, False), (429, None), (503, None)],
    )
    def test_pypi_status_codes(self, status, expected):
        import httpx2

        with patch.object(httpx2, "head") as head:
            head.return_value = httpx2.Response(status)
            ok, _note = pypi_is_published("https://pypi.org/project/a/")

        assert ok is expected

    def test_pypi_unreachable_is_no_answer(self):
        import httpx2

        with patch.object(httpx2, "head", side_effect=httpx2.ConnectError("down")):
            ok, _note = pypi_is_published("https://pypi.org/project/a/")

        assert ok is None

    @pytest.mark.django_db
    def test_no_answer_leaves_the_package_undecided(self, capsys):
        package = make_package("a")

        with patch(
            "probes.checkouts.subprocess.run",
            side_effect=subprocess.TimeoutExpired("git", 30),
        ):
            call_command("check_package_sources")

        package.refresh_from_db()
        assert package.probe is None
        assert package.probe_checked_at is None
        assert "no answer 1" in capsys.readouterr().out


@pytest.mark.django_db
class TestScanSkipsUnchangedCheckouts:
    @pytest.fixture()
    def checkout(self, repo_root):
        package = make_package("a")
        git = repo_root / "a" / ".git"
        git.mkdir(parents=True)
        (git / "HEAD").write_text("abc123\n")
        (repo_root / "a" / "models.py").write_text("from django.db import models\n")
        return package

    def test_a_second_scan_of_the_same_commit_is_skipped(self, checkout, capsys):
        call_command("scan_package_repos", "--package", "django")
        first = PackageProbe.objects.get(package=checkout).scanned_at

        call_command("scan_package_repos", "--package", "django")

        assert "unchanged 1" in capsys.readouterr().out
        assert PackageProbe.objects.get(package=checkout).scanned_at == first

    def test_force_rescans_it(self, checkout, capsys):
        call_command("scan_package_repos", "--package", "django")
        call_command("scan_package_repos", "--package", "django", "--force")

        assert "scanned 1  unchanged 0" in capsys.readouterr().out

    def test_a_new_commit_is_scanned(self, checkout, repo_root, capsys):
        call_command("scan_package_repos", "--package", "django")
        (repo_root / "a" / ".git" / "HEAD").write_text("def456\n")

        call_command("scan_package_repos", "--package", "django")

        assert PackageProbe.objects.get(package=checkout).commit == "def456"

    def test_different_libraries_are_scanned(self, checkout, capsys):
        call_command("scan_package_repos", "--package", "django")
        call_command("scan_package_repos", "--package", "django", "--package", "taggit")

        profile = PackageProbe.objects.get(package=checkout)
        assert profile.libraries == ["django", "taggit"]


@pytest.mark.django_db
class TestCatalogueStaleRows:
    @pytest.fixture()
    def profile(self):
        package = make_package("a")
        return baker.make(
            PackageProbe,
            package=package,
            symbols=[{"symbol": "django.urls.path", "count": 3, "library": "django"}],
            libraries=["django"],
        )

    def test_a_symbol_nobody_uses_is_zeroed(self, profile):
        call_command("build_probe_catalog")
        profile.symbols = []
        profile.save()

        call_command("build_probe_catalog")

        row = ProbeSymbol.objects.get(name="django.urls.path")
        assert (row.packages, row.uses) == (0, 0)

    def test_prune_still_removes_unannotated_rows(self, profile):
        call_command("build_probe_catalog")
        profile.symbols = []
        profile.save()

        call_command("build_probe_catalog", "--prune")

        assert not ProbeSymbol.objects.filter(name="django.urls.path").exists()

    def test_a_scoped_rebuild_leaves_other_libraries_alone(self, profile):
        other = baker.make(
            ProbeSymbol, kind="symbol", library="taggit", name="taggit.x", packages=7
        )

        call_command("build_probe_catalog", "--library", "django")

        other.refresh_from_db()
        assert other.packages == 7


class TestRemovalsTable:
    def test_the_json_table_loads(self):
        assert removals.load()["django.utils.six"] == "3.0"

    def test_the_table_matches_the_lookup(self):
        assert removals.REMOVED_IN == removals.load()


class TestReleasedVersions:
    def test_a_pre_release_counts_as_its_feature_release(self):
        assert django_docs.feature_release("6.1a1") == (6, 1)
        assert django_docs.feature_release("5.2.7") == (5, 2)

    def test_unreleased_removals_are_set_aside(self):
        done, unreleased = django_docs.released(
            {"django.a": "5.0", "django.b": "6.1"}, current="6.0.3"
        )

        assert done == {"django.a": "5.0"}
        assert unreleased == 1

    def test_one_point_ten_sorts_after_one_point_nine(self):
        assert django_docs.version_key("1.10") > django_docs.version_key("1.9")


@pytest.mark.django_db
class TestStatsCacheGeneration:
    @pytest.fixture()
    def real_cache(self, monkeypatch):
        cache = caches["waffle_cache_backend"]
        cache.clear()
        monkeypatch.setattr(stats, "cache", cache)
        yield cache
        cache.clear()

    def test_invalidate_rebuilds_on_next_read(self, real_cache):
        calls = []

        def builder():
            calls.append(now())
            return len(calls)

        assert stats.cached("x", builder) == 1
        assert stats.cached("x", builder) == 1

        stats.invalidate()

        assert stats.cached("x", builder) == 2
