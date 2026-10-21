"""Storing the probe profile and the dependency rows."""

import datetime

import pytest
from django.core.management import call_command
from django.db.models import Count, Q
from django.utils import timezone
from model_bakery import baker

from package.models import PackageDependency, PackageProbe
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

    def test_it_stores_one_row_per_dependency(self, cycles):
        make_package(
            "a", pypi_info={"requires_dist": ["django>=5.0", 'boto3; extra == "s3"']}
        )

        call_command("build_probe_profiles")

        rows = {d.name: d for d in PackageDependency.objects.all()}
        assert rows["django"].specifier == ">=5.0"
        assert rows["django"].extra == ""
        assert rows["boto3"].extra == "s3"

    def test_rerunning_does_not_duplicate_rows(self, cycles):
        make_package("a", pypi_info={"requires_dist": ["django>=5.0"]})

        call_command("build_probe_profiles")
        call_command("build_probe_profiles")

        assert PackageDependency.objects.count() == 1
        assert PackageProbe.objects.count() == 1

    def test_a_dependency_dropped_upstream_disappears(self, cycles):
        package = make_package(
            "a", pypi_info={"requires_dist": ["django>=5.0", "sqlparse"]}
        )
        call_command("build_probe_profiles")

        package.pypi_info = {"requires_dist": ["django>=5.0"]}
        package.save(update_fields=["pypi_info"])
        call_command("build_probe_profiles")

        assert list(PackageDependency.objects.values_list("name", flat=True)) == [
            "django"
        ]

    def test_a_dry_run_writes_nothing(self, cycles):
        make_package("a", pypi_info={"requires_dist": ["django>=5.0"]})

        call_command("build_probe_profiles", "--dry-run")

        assert not PackageProbe.objects.exists()
        assert not PackageDependency.objects.exists()

    def test_the_rollup_counts_packages_not_rows(self, cycles):
        """The query the dependency table exists for."""
        make_package("a", pypi_info={"requires_dist": ["django>=5.0"]})
        make_package("b", pypi_info={"requires_dist": ["django>=4.2", "boto3"]})
        make_package("c", pypi_info={"requires_dist": ['boto3; extra == "s3"']})

        call_command("build_probe_profiles")

        rows = (
            PackageDependency.objects.values("name")
            .annotate(
                packages=Count("package", distinct=True),
                core=Count("package", distinct=True, filter=Q(extra="")),
            )
            .order_by("-packages", "name")
        )
        counts = {r["name"]: (r["packages"], r["core"]) for r in rows}
        assert counts["django"] == (2, 2)
        assert counts["boto3"] == (2, 1)
