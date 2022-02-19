import pytest

from model_bakery import baker

from package.models import Category, Commit, Package, PackageExample, Version


@pytest.fixture()
def category(db) -> Category:
    return baker.make(Category)


@pytest.fixture()
def package(db) -> Package:
    return baker.make(Package)


@pytest.fixture()
def package_example(db) -> PackageExample:
    return baker.make(PackageExample)


@pytest.fixture()
def commit(db) -> Commit:
    return baker.make(Commit)


@pytest.fixture()
def version(db) -> Version:
    return baker.make(Version)
