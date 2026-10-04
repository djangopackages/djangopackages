import pytest
from model_bakery import baker

from grid.models import Element, Feature, Grid, GridPackage
from grid.tests import data


@pytest.fixture()
def grid(db) -> Grid:
    return baker.make(Grid)


@pytest.fixture()
def grid_package(db) -> GridPackage:
    return baker.make(GridPackage)


@pytest.fixture()
def feature(db) -> Feature:
    return baker.make(Feature)


@pytest.fixture()
def element(db) -> Element:
    return baker.make(Element)


@pytest.fixture()
def grid_test_data(db):
    """The shared grid fixture set, with the database-assigned pks."""
    return data.load()
