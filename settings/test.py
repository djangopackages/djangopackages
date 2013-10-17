# -*- coding: utf-8 -*-
"""Local test settings and globals which allows us to run our test suite
locally.
"""


from settings.base import *


########## DEBUG
DEBUG = True
TEMPLATE_DEBUG = DEBUG
SERVE_MEDIA = DEBUG


########## TEST
TEST_RUNNER = 'testrunner.OurCoverageRunner'

COVERAGE_MODULE_EXCLUDES = [
    'tests$', 'settings$', 'urls$', 'locale$',
    'migrations', 'fixtures', 'big_email_send$',
    'load_dev_data$', 'fix_grid_element$',
    'package_updater$', 'searchv2_build$', 'debug_toolbar',
    'pypi_updater', 'repo_updater'
]
COVERAGE_MODULE_EXCLUDES += PREREQ_APPS + ["djkombu", ]
COVERAGE_REPORT_HTML_OUTPUT_DIR = "coverage"

# from postgresify import postgresify
# DATABASES = postgresify()

########## DATABASES
# DATABASES = {
#     "default": {
#         "ENGINE": "django.db.backends.sqlite3",
#         "NAME": ":memory:",
#         "USER": "",
#         "PASSWORD": "",
#         "HOST": "",
#         "PORT": "",
#     },
# }
