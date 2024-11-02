import datetime
import logging

import pytest
from django.test.utils import override_settings


pytest_plugins = [
    "grid.tests.fixtures",
    "homepage.tests.fixtures",
    "package.tests.fixtures",
    "products.tests.fixtures",
]


TEST_SETTINGS = {
    "CACHES": {
        "default": {
            "BACKEND": "django.core.cache.backends.dummy.DummyCache",
            # "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        }
    },
    "CELERY_TASK_ALWAYS_EAGER": True,
    "EMAIL_BACKEND": "django.core.mail.backends.locmem.EmailBackend",
    "LOGGING_CONFIG": None,
    "PASSWORD_HASHERS": ["django.contrib.auth.hashers.MD5PasswordHasher"],
}


def pytest_configure(config):
    logging.disable(logging.CRITICAL)


@pytest.fixture(scope="session")
def django_db_setup(django_db_setup, django_db_blocker):
    """
    Tie to test database, cleanup at the end.
    """
    with django_db_blocker.unblock():
        yield


@pytest.fixture(autouse=True)
def set_time(time_machine):
    time_machine.move_to(datetime.datetime(2022, 2, 22, 2, 22))
    yield


@pytest.fixture(autouse=True, scope="session")
def use_test_settings():
    with override_settings(**TEST_SETTINGS):
        yield
