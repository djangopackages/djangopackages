import pytest

from model_bakery import baker


@pytest.fixture()
def product(db):
    return baker.make("products.Product", title="Django", slug="django")


@pytest.fixture()
def release(db, product):
    return baker.make("products.Release", product=product, cycle="lts")
