# -*- coding: utf-8 -*-
"""Local test settings and globals which allows us to run our test suite
locally.
"""


from settings.base import *


########## DEBUG
DEBUG = True
TEMPLATE_DEBUG = DEBUG

# serve media through the staticfiles app.
SERVE_MEDIA = DEBUG


########## TEST
TEST_RUNNER = 'testrunner.OurCoverageRunner'

COVERAGE_MODULE_EXCLUDES = [
    'tests$', 'settings$', 'urls$', 'locale$',
    'migrations', 'fixtures', 'big_email_send$',
    'load_dev_data$', 'fix_grid_element$',
    'package_updater$', 'searchv2_build$'
]
COVERAGE_MODULE_EXCLUDES += PREREQ_APPS + ["djkombu", ]
COVERAGE_REPORT_HTML_OUTPUT_DIR = "coverage"


########## DATABASES
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
        "USER": "",
        "PASSWORD": "",
        "HOST": "",
        "PORT": "",
    },
}
