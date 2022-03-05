"""Local test settings and globals which allows us to run our test suite
locally.
"""
import logging


from settings.base import *  # noqa


logging.disable(logging.CRITICAL)

LOGGING_CONFIG = None

########## DEBUG
DEBUG = False
TEMPLATES[0]["OPTIONS"]["debug"] = DEBUG
SERVE_MEDIA = DEBUG


########## TEST
# TEST_RUNNER = "testrunner.OurTestRunner"

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

if "debug_toolbar" in INSTALLED_APPS:
    INSTALLED_APPS.remove("debug_toolbar")

MIDDLEWARE = [
    middleware
    for middleware in MIDDLEWARE
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

