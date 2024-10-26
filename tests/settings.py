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


########## TEST
# TEST_RUNNER = "testrunner.OurTestRunner"

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

if "debug_toolbar" in INSTALLED_APPS:  # noqa
    INSTALLED_APPS.remove("debug_toolbar")  # noqa

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
