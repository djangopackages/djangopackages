"""Working out what a package supports, and what it depends on."""

import datetime

import pytest
from django.utils import timezone
from model_bakery import baker

from package.models import Package
from package.version_support import (
    declared_dependencies,
    released_cycles,
    version_support,
)

pytestmark = pytest.mark.django_db


@pytest.fixture()
def cycles(db):
    """Release cycles: some shipped, one undated, one still to come.

    Dates are relative to now because the suite runs on a frozen clock,
    and a hard-coded year quietly lands in the future and filters
    itself out.
    """
    released_cycles.cache_clear()
    today = timezone.now().date()
    shipped = today - datetime.timedelta(days=365)
    unshipped = today + datetime.timedelta(days=365)

    for slug, cycles_and_dates in (
        (
            "python",
            [
                ("3.9", shipped),
                ("3.10", shipped),
                ("3.11", shipped),
                ("3.98", unshipped),
                ("3.99", None),
            ],
        ),
        (
            "django",
            [
                ("4.2", shipped),
                ("5.0", shipped),
                ("5.1", shipped),
                ("9.8", unshipped),
                ("9.9", None),
            ],
        ),
    ):
        product = baker.make("products.Product", slug=slug, title=slug)
        for cycle, release in cycles_and_dates:
            baker.make(
                "products.Release", product=product, cycle=cycle, release=release
            )
    yield
    released_cycles.cache_clear()


def make_package(**kwargs):
    kwargs.setdefault("pypi_classifiers", [])
    kwargs.setdefault("pypi_requires_python", "")
    kwargs.setdefault("pypi_info", {})
    return Package(**kwargs)


class TestVersionSupport:
    def test_classifiers_win_because_they_name_exact_versions(self, cycles):
        package = make_package(
            pypi_classifiers=[
                "Programming Language :: Python :: 3.10",
                "Programming Language :: Python :: 3.11",
                "Framework :: Django :: 5.1",
            ],
            pypi_requires_python=">=3.9",
        )

        support = version_support(package)

        assert support.python == ("3.10", "3.11")
        assert support.python_source == "classifiers"
        assert support.python_range == "3.10 - 3.11"
        assert support.django == ("5.1",)

    def test_requires_python_is_resolved_when_there_are_no_classifiers(self, cycles):
        package = make_package(pypi_requires_python=">=3.10")

        support = version_support(package)

        assert support.python == ("3.10", "3.11")
        assert support.python_source == "requires_python"

    def test_an_unreleased_cycle_is_never_claimed(self, cycles):
        """ ">=3.10" must not promise a Python that does not exist yet.

        Both the undated cycle and the one dated in the future.
        """
        package = make_package(pypi_requires_python=">=3.10")

        python = version_support(package).python
        assert "3.99" not in python
        assert "3.98" not in python
        assert python == ("3.10", "3.11")

    def test_the_django_pin_is_resolved_from_requires_dist(self, cycles):
        package = make_package(pypi_info={"requires_dist": ["django>=5.0"]})

        support = version_support(package)

        assert support.django == ("5.0", "5.1")
        assert support.django_source == "requires_dist"

    def test_an_extra_is_not_evidence_of_django_support(self, cycles):
        """Celery declares Django under an extra; that does not make it a
        Django package."""
        package = make_package(
            pypi_info={"requires_dist": ['Django>=4.2; extra == "django"']}
        )

        support = version_support(package)

        assert support.django == ()
        assert support.django_source == ""

    def test_nothing_known_is_falsey(self, cycles):
        assert not version_support(make_package())

    def test_a_single_version_is_not_rendered_as_a_range(self, cycles):
        package = make_package(
            pypi_classifiers=["Programming Language :: Python :: 3.10"]
        )

        assert version_support(package).python_range == "3.10"


class TestDeclaredDependencies:
    def test_it_pulls_the_name_and_specifier_apart(self):
        package = make_package(
            pypi_info={"requires_dist": ["django>=4.2.9", "sqlparse>=0.2"]}
        )

        deps = declared_dependencies(package)

        assert [(d.name, d.specifier) for d in deps] == [
            ("django", ">=4.2.9"),
            ("sqlparse", ">=0.2"),
        ]
        assert all(not d.is_optional for d in deps)

    def test_an_extra_is_kept_but_marked(self):
        package = make_package(
            pypi_info={"requires_dist": ['boto3; extra == "s3"', "django"]}
        )

        deps = {d.name: d for d in declared_dependencies(package)}

        assert deps["boto3"].extra == "s3"
        assert deps["boto3"].is_optional
        assert not deps["django"].is_optional

    def test_names_are_normalised_so_they_group(self):
        package = make_package(pypi_info={"requires_dist": ["Django_Filter>=23"]})

        assert declared_dependencies(package)[0].name == "django-filter"

    def test_junk_is_skipped_rather_than_raising(self):
        package = make_package(
            pypi_info={"requires_dist": ["this is not a requirement", "django"]}
        )

        assert [d.name for d in declared_dependencies(package)] == ["django"]

    def test_no_metadata_is_not_an_error(self):
        """About half the catalogue predates requires_dist."""
        assert declared_dependencies(make_package()) == ()
