"""Local test settings and globals which allows us to run our test suite
locally.
"""

import logging

from settings import *  # noqa

logging.disable(logging.CRITICAL)

LOGGING_CONFIG = None

########## DEBUG
DEBUG = False
TEMPLATES[0]["OPTIONS"]["debug"] = DEBUG  # noqa
SERVE_MEDIA = DEBUG


# The fixture packages score 0. Tests that are about the cutoff set it
# themselves; the rest should not have to care that production uses 50.
PACKAGE_SCORE_MIN = 0

########## TEST
# TEST_RUNNER = "testrunner.OurTestRunner"

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

if "debug_toolbar" in INSTALLED_APPS:  # noqa
    INSTALLED_APPS.remove("debug_toolbar")  # noqa

DEBUG_TOOLBAR_CONFIG = {"IS_RUNNING_TESTS": False}

MIDDLEWARE = [
    middleware
    for middleware in MIDDLEWARE  # noqa
    if middleware
    not in [
        "debug_toolbar.middleware.DebugToolbarMiddleware",
        "whitenoise.middleware.WhiteNoiseMiddleware",
    ]
]

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.dummy.DummyCache",
    }
}

REDIS_URL = "redis://localhost:6379/0"
