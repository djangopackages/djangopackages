import logging
import datetime
import pytest


pytest_plugins = [
    "grid.tests.fixtures",
    "package.tests.fixtures",
]


def pytest_configure(config):
    logging.disable(logging.CRITICAL)


@pytest.fixture(autouse=True)
def set_time(time_machine):
    time_machine.move_to(datetime.datetime(2022, 2, 22, 2, 22))
    yield
