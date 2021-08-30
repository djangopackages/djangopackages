"""Local test settings and globals which allows us to run our test suite
locally.
"""
import logging


from settings.base import *


logging.disable(logging.CRITICAL)


########## DEBUG
DEBUG = False
TEMPLATES[0]["OPTIONS"]["debug"] = False


########## TEST
# TEST_RUNNER = "testrunner.OurTestRunner"

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

MIDDLEWARE = [
    middleware
    for middleware in MIDDLEWARE
    if middleware != "whitenoise.middleware.WhiteNoiseMiddleware"
]
