from package.scores import update_package_score
import pytest


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
    # score should be -100
    # abandoned for 2 years = loss 10% for each 3 months = 80% of the stars
    # + a -30% for not supporting python 3
    assert package_abandoned.repo_watchers == 1000
    update_package_score(package_abandoned, save=True)
    assert package_abandoned.score == -100


def test_package_abandoned_ten_years_score(package_abandoned_ten_years):
    # package_abandoned_ten_years.calculate_score()
    # score should be -100
    # abandoned for 2 years = loss 10% for each 3 months = 80% of the stars
    # + a -30% for not supporting python 3
    assert package_abandoned_ten_years.repo_watchers == 1000
    update_package_score(package_abandoned_ten_years, save=True)
    assert package_abandoned_ten_years.score == -500.0


def test_package_example(package_example):
    assert str(package_example) == f"{package_example.title}"

    # check that pacages are not active by default
    assert package_example.active is None
