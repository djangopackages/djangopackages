"""Storing the probe profile and the dependency rows."""

import datetime

import pytest
from django.core.management import call_command
from django.db import connection
from django.utils import timezone
from model_bakery import baker

from probes.models import PackageProbe
from probes.version_support import release_dates

pytestmark = pytest.mark.django_db


@pytest.fixture()
def cycles(db):
    release_dates.cache_clear()
    shipped = timezone.now().date() - datetime.timedelta(days=365)
    product = baker.make("products.Product", slug="django", title="django")
    for cycle in ("4.2", "5.0", "5.1"):
        baker.make("products.Release", product=product, cycle=cycle, release=shipped)
    yield
    release_dates.cache_clear()


def make_package(slug, **kwargs):
    kwargs.setdefault("pypi_classifiers", [])
    kwargs.setdefault("pypi_info", {})
    return baker.make(
        "package.Package",
        slug=slug,
        title=slug,
        repo_url=f"https://github.com/x/{slug}",
        pypi_url=f"https://pypi.org/project/{slug}/",
        score=10,
        **kwargs,
    )


class TestBuildProbeProfiles:
    def test_it_stores_versions_as_lists(self, cycles):
        make_package(
            "a",
            pypi_classifiers=[
                "Programming Language :: Python :: 3.11",
                "Framework :: Django :: 5.1",
            ],
        )

        call_command("build_probe_profiles")

        profile = PackageProbe.objects.get(package__slug="a")
        assert profile.python_versions == ["3.11"]
        assert profile.django_versions == ["5.1"]
        assert profile.python_source == "classifiers"
        assert profile.framework_versions == {}
        assert profile.metadata_updated_at is not None

    def test_it_stores_other_framework_versions_by_framework(self, cycles):
        make_package(
            "w",
            pypi_classifiers=[
                "Framework :: Django :: 5.2",
                "Framework :: Wagtail :: 7",
                "Framework :: Wagtail :: 8",
                "Framework :: Django CMS :: 5.1",
            ],
        )

        call_command("build_probe_profiles")

        profile = PackageProbe.objects.get(package__slug="w")
        assert profile.framework_versions == {
            "wagtail": ["7", "8"],
            "django-cms": ["5.1"],
        }
        assert profile.wagtail_range == "7 - 8"
        assert profile.django_cms_range == "5.1"

    def test_it_stores_dependencies_as_a_list_of_objects(self, cycles):
        make_package(
            "a", pypi_info={"requires_dist": ["django>=5.0", 'boto3; extra == "s3"']}
        )

        call_command("build_probe_profiles")

        profile = PackageProbe.objects.get(package__slug="a")
        by_name = {d["name"]: d for d in profile.dependencies}
        assert by_name["django"]["specifier"] == ">=5.0"
        assert by_name["django"]["extra"] == ""
        assert by_name["boto3"]["extra"] == "s3"
        assert [d["name"] for d in profile.required] == ["django"]
        assert [d["name"] for d in profile.optional] == ["boto3"]

    def test_rerunning_does_not_duplicate_anything(self, cycles):
        make_package("a", pypi_info={"requires_dist": ["django>=5.0"]})

        call_command("build_probe_profiles")
        call_command("build_probe_profiles")

        assert PackageProbe.objects.count() == 1
        assert len(PackageProbe.objects.get().dependencies) == 1

    def test_a_dependency_dropped_upstream_disappears(self, cycles):
        package = make_package(
            "a", pypi_info={"requires_dist": ["django>=5.0", "sqlparse"]}
        )
        call_command("build_probe_profiles")

        package.pypi_info = {"requires_dist": ["django>=5.0"]}
        package.save(update_fields=["pypi_info"])
        call_command("build_probe_profiles")

        profile = PackageProbe.objects.get(package__slug="a")
        assert [d["name"] for d in profile.dependencies] == ["django"]

    def test_a_dry_run_writes_nothing(self, cycles):
        make_package("a", pypi_info={"requires_dist": ["django>=5.0"]})

        call_command("build_probe_profiles", "--dry-run")

        assert not PackageProbe.objects.exists()

    def test_the_rollup_still_works_over_json(self, cycles):
        """Grouping survives the move to JSON, via jsonb_array_elements."""
        make_package("a", pypi_info={"requires_dist": ["django>=5.0"]})
        make_package("b", pypi_info={"requires_dist": ["django>=4.2", "boto3"]})
        make_package("c", pypi_info={"requires_dist": ['boto3; extra == "s3"']})

        call_command("build_probe_profiles")

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT dep->>'name' AS name,
                       count(DISTINCT p.package_id) AS packages,
                       count(DISTINCT p.package_id)
                           FILTER (WHERE dep->>'extra' = '') AS core
                FROM probes_packageprobe p,
                     jsonb_array_elements(p.dependencies) AS dep
                GROUP BY 1
                ORDER BY packages DESC, name
                """
            )
            counts = {row[0]: (row[1], row[2]) for row in cursor.fetchall()}

        assert counts["django"] == (2, 2)
        assert counts["boto3"] == (2, 1)


class TestScanStoresSymbols:
    """scan_package_repos writing the AST half of the profile."""

    @pytest.fixture()
    def checkout(self, settings, tmp_path):
        settings.PACKAGE_REPO_ROOT = tmp_path
        package = make_package("a")
        root = tmp_path / "a"
        (root / ".git").mkdir(parents=True)
        (root / "models.py").write_text(
            "from django.db import models\n"
            "from django.conf import settings\n"
            "x = models.CharField\n"
            "y = models.CharField\n"
            "z = settings.DEBUG\n"
        )
        return package, root

    def test_symbols_are_a_list_of_objects_most_used_first(self, checkout):
        call_command("scan_package_repos", "--totals-only")

        profile = PackageProbe.objects.get(package__slug="a")
        assert isinstance(profile.symbols, list)
        assert all(
            {"symbol", "count", "library"} == set(row) for row in profile.symbols
        )
        assert {row["library"] for row in profile.symbols} == {"django"}
        counts = [row["count"] for row in profile.symbols]
        assert counts == sorted(counts, reverse=True)

    def test_it_counts_repeated_use(self, checkout):
        call_command("scan_package_repos", "--totals-only")

        profile = PackageProbe.objects.get(package__slug="a")
        assert profile.symbol_counts["django.db.models.CharField"] == 2
        assert profile.files_scanned == 1

    def test_it_records_the_commit_it_read(self, checkout):
        """Read off disk, not from git, so the scan stays a file reader."""
        _, root = checkout
        (root / ".git" / "HEAD").write_text("ref: refs/heads/main\n")
        (root / ".git" / "refs" / "heads").mkdir(parents=True)
        (root / ".git" / "refs" / "heads" / "main").write_text("abc123\n")

        call_command("scan_package_repos", "--totals-only")

        assert PackageProbe.objects.get(package__slug="a").commit == "abc123"

    def test_a_detached_head_is_read_directly(self, checkout):
        _, root = checkout
        (root / ".git" / "HEAD").write_text("deadbeef\n")

        call_command("scan_package_repos", "--totals-only")

        assert PackageProbe.objects.get(package__slug="a").commit == "deadbeef"

    def test_packed_refs_are_used_when_there_is_no_loose_ref(self, checkout):
        """A fresh clone keeps its refs packed."""
        _, root = checkout
        (root / ".git" / "HEAD").write_text("ref: refs/heads/main\n")
        (root / ".git" / "packed-refs").write_text(
            "# pack-refs with: peeled fully-peeled sorted\n"
            "cafe1234 refs/heads/main\n"
            "^99999999\n"
        )

        call_command("scan_package_repos", "--totals-only")

        assert PackageProbe.objects.get(package__slug="a").commit == "cafe1234"

    def test_an_unreadable_commit_does_not_fail_the_scan(self, checkout):
        call_command("scan_package_repos", "--totals-only")

        profile = PackageProbe.objects.get(package__slug="a")
        assert profile.commit == ""
        assert profile.symbols

    def test_a_dry_run_saves_nothing(self, checkout):
        call_command("scan_package_repos", "--totals-only", "--dry-run")

        assert not PackageProbe.objects.exists()

    def test_rescanning_replaces_rather_than_appends(self, checkout):
        call_command("scan_package_repos", "--totals-only")
        first = len(PackageProbe.objects.get(package__slug="a").symbols)

        call_command("scan_package_repos", "--totals-only")

        assert len(PackageProbe.objects.get(package__slug="a").symbols) == first
        assert PackageProbe.objects.count() == 1

    def test_the_metadata_half_is_left_alone(self, checkout):
        """A scan must not wipe what build_probe_profiles wrote."""
        package, _ = checkout
        PackageProbe.objects.create(
            package=package, python_versions=["3.12"], django_versions=["5.2"]
        )

        call_command("scan_package_repos", "--totals-only")

        profile = PackageProbe.objects.get(package__slug="a")
        assert profile.python_versions == ["3.12"]
        assert profile.django_versions == ["5.2"]
        assert profile.symbols


class TestScanStoresPatterns:
    """The pattern half of the AST scan, stored alongside the symbols."""

    @pytest.fixture()
    def checkout(self, settings, tmp_path):
        settings.PACKAGE_REPO_ROOT = tmp_path
        package = make_package("b")
        root = tmp_path / "b"
        (root / ".git").mkdir(parents=True)
        (root / "views.py").write_text(
            "from django.conf import settings\n"
            "from django.db import transaction\n"
            "@transaction.atomic\n"
            "def view():\n"
            "    return settings.AUTH_USER_MODEL\n"
        )
        return package, root

    def test_patterns_are_a_list_of_objects_most_hit_first(self, checkout):
        call_command("scan_package_repos", "--totals-only")

        profile = PackageProbe.objects.get(package__slug="b")
        assert isinstance(profile.patterns, list)
        assert all({"pattern", "count"} == set(row) for row in profile.patterns)
        counts = [row["count"] for row in profile.patterns]
        assert counts == sorted(counts, reverse=True)
        assert profile.pattern_counts["probe:transaction_atomic"] == 1

    def test_the_settings_a_package_reads_survive_the_round_trip(self, checkout):
        call_command("scan_package_repos", "--totals-only")

        profile = PackageProbe.objects.get(package__slug="b")
        assert profile.settings_used == {"AUTH_USER_MODEL": 1}

    def test_rescanning_replaces_the_patterns(self, checkout):
        _, root = checkout
        call_command("scan_package_repos", "--totals-only")
        (root / "views.py").write_text("x = 1\n")

        call_command("scan_package_repos", "--totals-only")

        assert PackageProbe.objects.get(package__slug="b").patterns == []

    def test_a_dry_run_stores_no_patterns(self, checkout):
        call_command("scan_package_repos", "--totals-only", "--dry-run")

        assert not PackageProbe.objects.filter(package__slug="b").exists()

    def test_the_rollup_over_patterns_is_one_query(self, checkout):
        """Who uses a pattern at all, which is the question worth asking."""
        call_command("scan_package_repos", "--totals-only")

        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT pattern->>'pattern', count(DISTINCT p.package_id)
                FROM probes_packageprobe p,
                     jsonb_array_elements(p.patterns) AS pattern
                GROUP BY 1 ORDER BY 2 DESC, 1
                """
            )
            rows = cursor.fetchall()

        assert ("probe:transaction_atomic", 1) in rows
