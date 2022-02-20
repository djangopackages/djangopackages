def test_category(category):
    assert str(category) == f"{category.title}"


def test_commit(commit):
    assert str(commit) == f"Commit for '{commit.package.title}' on {commit.commit_date}"


def test_package(package):
    assert str(package) == f"{package.title}"
    assert package.is_deprecated is False
    assert package.get_pypi_uri() is None
    assert package.get_pypi_json_uri() is None
    assert package.date_deprecated is None
    assert package.date_repo_archived is None
    assert package.deprecated_by is None
    assert package.deprecates_package is None
    assert package.last_updated
    assert package.license_latest == "UNKNOWN"
    assert package.pypi_classifiers is None
    assert package.pypi_license is None
    assert package.pypi_licenses is None
    assert package.pypi_name == ""
    assert package.pypi_requires_python is None
    assert package.score == 0.0
    assert package.supports_python3 is None
    assert package.version_set.count() == 0


def test_package_example(package_example):
    assert str(package_example) == f"{package_example.title}"


# def test_version(version):
#     assert True
