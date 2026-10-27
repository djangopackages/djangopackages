"""Working out what a package supports, and what it depends on."""

import datetime

import pytest
from django.utils import timezone
from model_bakery import baker

from package.models import Package
from probes.version_support import (
    bounded_above,
    declared_dependencies,
    release_dates,
    released_cycles,
    version_support,
)

pytestmark = pytest.mark.django_db


@pytest.fixture()
def cycles(db):
    """Release cycles: three shipped years apart, one undated, one to come.

    Dates are relative to now because the suite runs on a frozen clock,
    and a hard-coded year quietly lands in the future and filters
    itself out. The three shipped cycles are spread out rather than
    stacked on one day so a package published between them can only
    reach the ones that already existed.
    """
    release_dates.cache_clear()
    today = timezone.now().date()
    old = today - datetime.timedelta(days=1000)
    middle = today - datetime.timedelta(days=700)
    recent = today - datetime.timedelta(days=365)
    unshipped = today + datetime.timedelta(days=365)

    for slug, cycles_and_dates in (
        (
            "python",
            [
                ("3.9", old),
                ("3.10", middle),
                ("3.11", recent),
                ("3.98", unshipped),
                ("3.99", None),
            ],
        ),
        (
            "django",
            [
                ("4.2", old),
                ("5.0", middle),
                ("5.1", recent),
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
    release_dates.cache_clear()


def make_package(*, published=None, **kwargs):
    """A package, optionally with the date of its latest PyPI release.

    Left unsaved when no date is needed, since most of these tests only
    read metadata straight off the instance.
    """
    kwargs.setdefault("pypi_classifiers", [])
    kwargs.setdefault("pypi_requires_python", "")
    kwargs.setdefault("pypi_info", {})
    if published is None:
        return Package(**kwargs)

    package = baker.make("package.Package", **kwargs)
    package.latest_version = baker.make(
        "package.Version",
        package=package,
        number="1.0",
        upload_time=timezone.make_aware(
            datetime.datetime.combine(published, datetime.time(12))
        ),
    )
    package.save(update_fields=["latest_version"])
    return package


def days_ago(days: int) -> datetime.date:
    return timezone.now().date() - datetime.timedelta(days=days)


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

    def test_wagtail_and_django_cms_classifiers_are_kept_by_framework(self, cycles):
        package = make_package(
            pypi_classifiers=[
                "Framework :: Wagtail",
                "Framework :: Wagtail :: 8",
                "Framework :: Wagtail :: 7",
                "Framework :: Django CMS :: 5.1",
                "Framework :: Django CMS :: 4.1",
                "Framework :: Django CMS :: 5.0",
            ],
        )

        support = version_support(package)

        assert support.frameworks == {
            "wagtail": ("7", "8"),
            "django-cms": ("4.1", "5.0", "5.1"),
        }
        assert support.framework_range("wagtail") == "7 - 8"
        assert support.framework_range("django-cms") == "4.1 - 5.1"
        assert support.framework_range("flask") == ""
        assert support.django == ()
        assert support

    def test_a_bare_framework_classifier_names_no_version(self, cycles):
        package = make_package(pypi_classifiers=["Framework :: Wagtail"])
        assert version_support(package).frameworks == {}

    def test_requires_python_is_resolved_when_there_are_no_classifiers(self, cycles):
        package = make_package(pypi_requires_python=">=3.10", published=days_ago(1))

        support = version_support(package)

        assert support.python == ("3.10", "3.11")
        assert support.python_source == "requires_python"

    def test_an_unreleased_cycle_is_never_claimed(self, cycles):
        """ ">=3.10" must not promise a Python that does not exist yet.

        Both the undated cycle and the one dated in the future.
        """
        package = make_package(pypi_requires_python=">=3.10", published=days_ago(1))

        python = version_support(package).python
        assert "3.99" not in python
        assert "3.98" not in python
        assert python == ("3.10", "3.11")

    def test_the_django_pin_is_resolved_from_requires_dist(self, cycles):
        package = make_package(
            pypi_info={"requires_dist": ["django>=5.0"]}, published=days_ago(1)
        )

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


class TestOpenEndedSpecifiers:
    """`Django>=1.8` is a minimum, not a promise about every later cycle."""

    def test_a_pin_is_read_as_of_the_release_that_declared_it(self, cycles):
        """An old release cannot have been tested against a later Django."""
        package = make_package(
            pypi_info={"requires_dist": ["django>=4.2"]}, published=days_ago(800)
        )

        support = version_support(package)

        # 5.0 and 5.1 both shipped after this release went out.
        assert support.django == ("4.2",)
        assert support.django_source == "requires_dist"

    def test_requires_python_is_capped_the_same_way(self, cycles):
        package = make_package(pypi_requires_python=">=3.9", published=days_ago(800))

        support = version_support(package)

        assert support.python == ("3.9",)
        assert support.python_source == "requires_python"

    def test_an_undateable_release_claims_nothing(self, cycles):
        """With no publication date there is nothing to read the pin
        against, and a lower bound alone is not evidence of support."""
        package = make_package(pypi_info={"requires_dist": ["django>=4.2"]})

        support = version_support(package)

        assert support.django == ()
        assert support.django_source == ""

    def test_an_upper_bound_is_trusted_whatever_the_date(self, cycles):
        """A maintainer who wrote <5.1 said what they meant."""
        package = make_package(
            pypi_info={"requires_dist": ["django>=4.2,<5.1"]}, published=days_ago(800)
        )

        assert version_support(package).django == ("4.2", "5.0")

    def test_classifiers_are_never_capped(self, cycles):
        """They name exact versions, so the date adds nothing."""
        package = make_package(
            pypi_classifiers=[
                "Framework :: Django :: 4.2",
                "Framework :: Django :: 5.1",
            ],
            published=days_ago(800),
        )

        assert version_support(package).django == ("4.2", "5.1")


class TestBoundedAbove:
    def test_what_counts_as_an_upper_bound(self, subtests):
        cases = [
            (">=4.2", False),
            ("", False),
            ("!=4.2", False),
            (">4.1", False),
            ("<5.1", True),
            ("<=5.1", True),
            (">=4.2,<5.1", True),
            ("==4.2.*", True),
            ("~=4.2", True),
            ("===4.2", True),
            ("not a specifier", False),
        ]
        for specifier, expected in cases:
            with subtests.test(specifier=specifier):
                assert bounded_above(specifier) is expected


class TestReleasedCycles:
    def test_it_reports_what_had_shipped_on_a_given_day(self, cycles):
        assert released_cycles("django", on=days_ago(800)) == ("4.2",)
        assert released_cycles("django", on=days_ago(500)) == ("4.2", "5.0")
        assert released_cycles("django") == ("4.2", "5.0", "5.1")

    def test_an_unshipped_cycle_is_never_included(self, cycles):
        every = released_cycles("django", on=days_ago(0))
        assert "9.8" not in every
        assert "9.9" not in every


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
