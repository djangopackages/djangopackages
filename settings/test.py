"""Local test settings and globals which allows us to run our test suite
locally.
"""
import logging


from settings.base import *


logging.disable(logging.CRITICAL)


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
