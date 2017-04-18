# -*- coding: utf-8 -*-
"""Local test settings and globals which allows us to run our test suite
locally.
"""


from settings.base import *


########## DEBUG
DEBUG = True
TEMPLATES[0]['OPTIONS']['debug'] = DEBUG
SERVE_MEDIA = DEBUG


########## TEST
TEST_RUNNER = 'testrunner.OurTestRunner'

PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
]
