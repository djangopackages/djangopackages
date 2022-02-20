def test_category(category):
    assert str(category) == f"{category.title}"


def test_commit(commit):
    assert str(commit) == f"Commit for '{commit.package.title}' on {commit.commit_date}"


def test_package(package):
    assert str(package) == f"{package.title}"
    assert package.is_deprecated is False
    assert package.get_pypi_uri()
    assert package.get_pypi_json_uri()
    assert package.pypi_name()
    assert package.repo
    assert package.last_updated


def test_package_example(package_example):
    assert str(package_example) == f"{package_example.title}"


# def test_version(version):
#     assert True
