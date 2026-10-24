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


class TestTheFrameworkItself:
    def test_django_is_never_checked_out(self, repo_root):
        """Its source defines the symbols we count rather than using them."""
        baker.make(
            "package.Package",
            slug="django",
            repo_url="https://github.com/django/django",
            pypi_url="https://pypi.org/project/Django/",
            score=100,
        )

        with patch("probes.checkouts.subprocess.run") as run:
            call_command("sync_package_repos")

        run.assert_not_called()

    def test_a_package_merely_named_after_it_is_kept(self, repo_root):
        baker.make(
            "package.Package",
            slug="django-extensions",
            repo_url="https://github.com/django-extensions/django-extensions",
            pypi_url="https://pypi.org/project/django-extensions/",
            score=10,
        )

        from probes.checkouts import scannable_packages

        assert scannable_packages().count() == 1


class TestTheSizeCap:
    """A cap on checkouts we could clone but would rather not keep."""

    def _package(self, slug="big"):
        return baker.make(
            "package.Package",
            slug=slug,
            repo_url=f"https://github.com/x/{slug}",
            pypi_url=f"https://pypi.org/project/{slug}/",
            score=1,
        )

    def test_an_oversized_checkout_is_discarded_and_marked_unwanted(self, repo_root):
        package = self._package()

        with (
            patch("probes.pipeline.sync_checkout") as sync,
            patch(
                "probes.pipeline.checkout_size",
                return_value=600 * 1024 * 1024,
            ),
            patch("probes.pipeline.discard_checkout") as discard,
        ):
            sync.return_value = (repo_root / "big", "cloned")
            call_command("sync_package_repos", "--max-mb", "500")

        package.refresh_from_db()
        assert package.probe_wanted is False
        assert "600MB" in package.probe_wanted_note
        assert package.probe_bytes == 600 * 1024 * 1024
        discard.assert_called_once()

    def test_it_is_then_left_alone_on_later_runs(self, repo_root):
        package = self._package()
        package.probe_wanted = False
        package.save()

        with patch("probes.checkouts.subprocess.run") as run:
            call_command("sync_package_repos")

        run.assert_not_called()

    def test_a_checkout_under_the_cap_is_kept_and_measured(self, repo_root):
        package = self._package(slug="small")

        with (
            patch("probes.pipeline.sync_checkout") as sync,
            patch(
                "probes.pipeline.checkout_size",
                return_value=5 * 1024 * 1024,
            ),
            patch("probes.pipeline.discard_checkout") as discard,
        ):
            sync.return_value = (repo_root / "small", "cloned")
            call_command("sync_package_repos", "--max-mb", "500")

        package.refresh_from_db()
        assert package.probe_wanted is None
        assert package.probe_bytes == 5 * 1024 * 1024
        discard.assert_not_called()

    def test_size_is_recorded_even_with_no_cap(self, repo_root):
        package = self._package(slug="plain")

        with (
            patch("probes.pipeline.sync_checkout") as sync,
            patch(
                "probes.pipeline.checkout_size",
                return_value=7 * 1024 * 1024,
            ),
        ):
            sync.return_value = (repo_root / "plain", "cloned")
            call_command("sync_package_repos")

        package.refresh_from_db()
        assert package.probe_bytes == 7 * 1024 * 1024


class TestPruning:
    """A profile outlives the package leaving the probed set."""

    def test_djangos_own_profile_is_dropped(self, repo_root):
        from probes.models import PackageProbe

        package = baker.make(
            "package.Package",
            slug="django",
            repo_url="https://github.com/django/django",
            pypi_url="https://pypi.org/project/Django/",
            score=100,
        )
        baker.make(PackageProbe, package=package, files_scanned=9)

        call_command("prune_package_probes")

        assert PackageProbe.objects.count() == 0

    def test_a_package_we_still_probe_is_left_alone(self, repo_root):
        from probes.models import PackageProbe

        package = baker.make(
            "package.Package",
            slug="django-filter",
            repo_url="https://github.com/carltongibson/django-filter",
            pypi_url="https://pypi.org/project/django-filter/",
            score=10,
        )
        baker.make(PackageProbe, package=package, files_scanned=9)

        call_command("prune_package_probes")

        assert PackageProbe.objects.count() == 1

    def test_an_unwanted_package_loses_its_profile(self, repo_root):
        from probes.models import PackageProbe

        package = baker.make(
            "package.Package",
            slug="huge",
            repo_url="https://github.com/x/huge",
            pypi_url="https://pypi.org/project/huge/",
            score=10,
            probe_wanted=False,
        )
        baker.make(PackageProbe, package=package, files_scanned=9)

        call_command("prune_package_probes")

        assert PackageProbe.objects.count() == 0

    def test_a_dry_run_keeps_everything(self, repo_root):
        from probes.models import PackageProbe

        package = baker.make(
            "package.Package",
            slug="django",
            repo_url="https://github.com/django/django",
            pypi_url="https://pypi.org/project/Django/",
            score=100,
        )
        baker.make(PackageProbe, package=package, files_scanned=9)

        call_command("prune_package_probes", "--dry-run")

        assert PackageProbe.objects.count() == 1


class TestTheLimitCountsWork:
    """--limit counts what we fetched, not what we looked at."""

    def _packages(self, how_many, **kwargs):
        return [
            baker.make(
                "package.Package",
                slug=f"pkg-{i}",
                repo_url=f"https://github.com/x/pkg-{i}",
                pypi_url=f"https://pypi.org/project/pkg-{i}/",
                score=100 - i,
                **kwargs,
            )
            for i in range(how_many)
        ]

    def test_missing_only_reaches_past_the_packages_already_cloned(self, repo_root):
        """The bug: slicing took the same top rows and skipped them all."""
        self._packages(5)
        # the two highest scoring already have checkouts
        for slug in ["pkg-0", "pkg-1"]:
            (repo_root / slug / ".git").mkdir(parents=True)

        MOD = "probes.pipeline"
        with (
            patch(f"{MOD}.sync_checkout") as sync,
            patch(f"{MOD}.checkout_size", return_value=1024),
        ):
            sync.side_effect = lambda package, **kw: (
                repo_root / package.slug,
                "cloned",
            )
            call_command("sync_package_repos", "--missing-only", "--limit", "2")

        cloned = sorted(call.args[0].slug for call in sync.call_args_list)
        assert cloned == ["pkg-2", "pkg-3"]

    def test_the_limit_still_stops_at_the_limit(self, repo_root):
        self._packages(10)

        MOD = "probes.pipeline"
        with (
            patch(f"{MOD}.sync_checkout") as sync,
            patch(f"{MOD}.checkout_size", return_value=1024),
        ):
            sync.side_effect = lambda package, **kw: (
                repo_root / package.slug,
                "cloned",
            )
            call_command("sync_package_repos", "--limit", "3")

        assert sync.call_count == 3
