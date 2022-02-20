import pytest

from model_bakery import baker

from package.models import Category, Commit, Package, PackageExample, Version


@pytest.fixture()
def category(db) -> Category:
    return baker.make(Category)


@pytest.fixture()
def commit(db, package) -> Commit:
    return baker.make(Commit, package=package)


@pytest.fixture()
def package(db, category) -> Package:
    return baker.make(Package, category=category)


@pytest.fixture()
def package_example(db, package) -> PackageExample:
    return baker.make(PackageExample, package=package)


@pytest.fixture()
def version(db, package) -> Version:
    return baker.make(Version, package=package)
