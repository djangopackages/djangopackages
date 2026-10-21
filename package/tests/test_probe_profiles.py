"""Storing the probe profile and the dependency rows."""

import datetime

import pytest
from django.core.management import call_command
from django.db import connection
from django.utils import timezone
from model_bakery import baker

from package.models import PackageProbe
from package.version_support import released_cycles

pytestmark = pytest.mark.django_db


@pytest.fixture()
def cycles(db):
    released_cycles.cache_clear()
    shipped = timezone.now().date() - datetime.timedelta(days=365)
    product = baker.make("products.Product", slug="django", title="django")
    for cycle in ("4.2", "5.0", "5.1"):
        baker.make("products.Release", product=product, cycle=cycle, release=shipped)
    yield
    released_cycles.cache_clear()


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
        assert profile.metadata_updated_at is not None

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
                FROM package_packageprobe p,
                     jsonb_array_elements(p.dependencies) AS dep
                GROUP BY 1
                ORDER BY packages DESC, name
                """
            )
            counts = {row[0]: (row[1], row[2]) for row in cursor.fetchall()}

        assert counts["django"] == (2, 2)
        assert counts["boto3"] == (2, 1)
