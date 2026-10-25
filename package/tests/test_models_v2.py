from django.db import IntegrityError
from package.models import Package
from package.scores import update_package_score
import pytest
from model_bakery import baker


def test_category(category):
    assert str(category) == f"{category.title}"


def test_package(package):
    assert str(package) == f"{package.title}"
    assert package.is_deprecated is False
    assert package.get_pypi_uri() is None
    assert package.get_pypi_json_uri() is None
    assert package.date_deprecated is None
    assert package.date_repo_archived is None
    assert package.deprecated_by is None
    assert package.deprecates_package is None
    assert package.last_commit_date
    assert package.pypi_classifiers is None
    assert package.pypi_license is None
    assert package.pypi_licenses is None
    assert package.pypi_license_display == "UNKNOWN"
    assert package.pypi_name == ""
    assert package.pypi_requires_python is None
    assert package.score == 0.0
    assert package.supports_python3 is None
    assert package.version_set.count() == 0


def test_package_pypi_name(package):
    assert package.pypi_name == ""

    package.pypi_url = "django"
    assert package.pypi_name == "django"

    package.pypi_url = "/django/"
    assert package.pypi_name == "django"

    package.pypi_url = "http://pypi.python.org/pypi/django"
    assert package.pypi_name == "django"

    package.pypi_url = "https://pypi.python.org/pypi/django"
    assert package.pypi_name == "django"

    package.pypi_url = "https://pypi.org/project/django"
    assert package.pypi_name == "django"

    assert package.get_pypi_uri() == "https://pypi.org/project/django/"
    assert package.get_pypi_json_uri() == "https://pypi.org/pypi/django/json"


def test_version_order(package_cms):
    versions = package_cms.version_set.by_version()
    expected_values = [
        "2.0.0",
        "2.0.1",
        "2.0.2",
        "2.1.0",
        # "2.1.0.beta3",
        # "2.1.0.rc1",
        # "2.1.0.rc2",
        # "2.1.0.rc3",
        "2.1.1",
        "2.1.2",
        "2.1.3",
    ]
    returned_values = [v.number for v in versions]
    assert returned_values == expected_values


@pytest.mark.xfail(reason="inconsistent state between GH CI and local")
def test_package_score(package_cms):
    assert package_cms.score != package_cms.repo_watchers
    # assert package_cms.calculate_score() == package_cms.repo_watchers
    package_cms.calculate_score()
    # we save / update. Value is saved for grid order
    package_cms.save()

    package_cms.refresh_from_db()
    assert package_cms.score == package_cms.repo_watchers

    # to trigger local failure
    assert False


def test_package_abandoned_score(package_abandoned):
    # Two years without a commit or release loses both activity rules
    # (40 of 160 points) but is not yet dormant, so the score stays above 0.
    assert package_abandoned.repo_watchers == 1000
    update_package_score(package_abandoned, save=True)
    assert 0 < package_abandoned.score <= 75


def test_package_abandoned_ten_years_score(package_abandoned_ten_years):
    # Ten years idle, but still 26,257 downloads a month: in use, so not
    # dormant. Drop the downloads and it is a hard zero however many stars.
    package = package_abandoned_ten_years
    assert package.repo_watchers == 1000
    assert package.pypi_downloads >= Package.DORMANT_MIN_DOWNLOADS
    update_package_score(package, save=True)
    assert not package.is_dormant
    assert 0 < package.score <= 75

    package.pypi_downloads = 100
    update_package_score(package, save=True)
    assert package.is_dormant
    assert package.score == 0


def test_package_example(package_example):
    assert str(package_example) == f"{package_example.title}"

    # check that pacages are not active by default
    assert package_example.active is None


def test_version_number_unique_per_package(package):
    baker.make("package.Version", package=package, number="1.0.0")

    with pytest.raises(IntegrityError):
        baker.make("package.Version", package=package, number="1.0.0")


def test_version_number_can_repeat_across_packages(category):
    first_package = baker.make(
        "package.Package",
        category=category,
        repo_url="https://github.com/django/first-package",
    )
    second_package = baker.make(
        "package.Package",
        category=category,
        repo_url="https://github.com/django/second-package",
    )

    baker.make("package.Version", package=first_package, number="1.0.0")
    baker.make("package.Version", package=second_package, number="1.0.0")

    assert first_package.version_set.count() == 1
    assert second_package.version_set.count() == 1


def test_package_pypi_ancient_none_when_upload_time_missing(category):
    package = baker.make("package.Package", category=category)
    version = baker.make("package.Version", package=package, upload_time=None)
    package.latest_version = version
    package.save(update_fields=["latest_version"])

    assert package.pypi_ancient is None
