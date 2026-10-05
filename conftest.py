import datetime
import logging

import pytest
from django.conf import settings
from django.core.cache import caches
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
        },
        "waffle_cache_backend": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "unique-snowflake",
        },
    },
    "EMAIL_BACKEND": "django.core.mail.backends.locmem.EmailBackend",
    "LOGGING_CONFIG": None,
    "PASSWORD_HASHERS": ["django.contrib.auth.hashers.MD5PasswordHasher"],
    # Note:
    # By setting the Waffle cache to a LocMemCache instead of DummyCache,
    # we can avoid the overhead of hitting the database for each waffle
    # query for FLags, Switches, and Samples, which is increasing the number
    # of queries made in testing mode by at least 5.
    "WAFFLE_CACHE_NAME": "waffle_cache_backend",
    "WAFFLE_CREATE_MISSING_SWITCHES": False,
    "WAFFLE_CREATE_MISSING_FLAGS": False,
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
def cold_waffle_cache():
    """Start every test with the waffle cache empty.

    WAFFLE_CACHE_NAME above is a LocMemCache, and it lives for the whole
    session, so whichever test read a flag first paid its queries and every
    test after it got them free. That made assertNumQueries depend on
    pytest-randomly's seed: the same test wanted 8 queries in one run and 7
    in the next, and CI went red on main often enough to block a deploy.

    Clearing it here means every test loads its own flags, so the counts
    below are the ones a request actually makes on a cold cache and they do
    not move with the order.
    """
    caches[settings.WAFFLE_CACHE_NAME].clear()
    yield


@pytest.fixture(autouse=True)
def set_time(time_machine):
    time_machine.move_to(datetime.datetime(2022, 2, 22, 2, 22))
    yield


@pytest.fixture(autouse=True, scope="session")
def use_test_settings():
    with override_settings(**TEST_SETTINGS):
        yield
