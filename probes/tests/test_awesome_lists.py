"""A curated list is kept as a checkout even though it is not a package."""

from unittest.mock import patch

import pytest
from model_bakery import baker

from package.models import PackageTag
from probes.checkouts import scannable_packages
from probes.pipeline import check_source

pytestmark = pytest.mark.django_db


def _list(slug="awesome-django", **extra):
    return baker.make(
        "package.Package",
        slug=slug,
        repo_url=f"https://github.com/wsvincent/{slug}",
        pypi_url="",
        score=-40,
        tags=[PackageTag.AWESOME_LIST],
        **extra,
    )


class TestScannablePackages:
    def test_a_tagged_list_is_kept_without_a_release_or_a_score(self):
        _list()
        assert list(scannable_packages().values_list("slug", flat=True)) == [
            "awesome-django"
        ]

    def test_an_untagged_repo_without_a_release_is_still_skipped(self):
        baker.make(
            "package.Package",
            slug="someones-fork",
            repo_url="https://github.com/x/someones-fork",
            pypi_url="",
            score=50,
        )
        assert scannable_packages().count() == 0

    def test_saying_no_still_wins(self):
        _list(probe_wanted=False)
        assert scannable_packages().count() == 0


class TestCheckSource:
    def test_the_repo_answering_is_enough_for_a_list(self):
        package = _list()
        with (
            patch("probes.pipeline.repo_is_reachable", return_value=(True, "")),
            patch("probes.pipeline.pypi_is_published") as pypi,
        ):
            ok, _note = check_source(package)

        assert ok is True
        pypi.assert_not_called()
        package.refresh_from_db()
        assert package.probe is True

    def test_an_ordinary_package_is_still_asked_about_pypi(self):
        package = baker.make(
            "package.Package",
            slug="django-x",
            repo_url="https://github.com/x/django-x",
            pypi_url="https://pypi.org/project/django-x/",
        )
        with (
            patch("probes.pipeline.repo_is_reachable", return_value=(True, "")),
            patch(
                "probes.pipeline.pypi_is_published", return_value=(False, "gone")
            ) as pypi,
        ):
            ok, note = check_source(package)

        pypi.assert_called_once()
        assert (ok, note) == (False, "gone")


class TestTheTag:
    def test_packages_start_with_no_tags(self, package):
        assert package.tags == []
        assert package.is_awesome_list is False

    def test_is_awesome_list_reads_the_tag(self):
        assert _list().is_awesome_list is True
