# -*- coding: utf-8 -*-
# Django settings

import os.path
from os import environ

from django.template.defaultfilters import slugify

PROJECT_ROOT = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

DEBUG = True
TEMPLATE_DEBUG = DEBUG

# serve media through the staticfiles app.
SERVE_MEDIA = DEBUG

INTERNAL_IPS = [
    "127.0.0.1",
]

ADMINS = [
    ("Daniel Greenfeld", "pydanny@gmail.com"),
]

MANAGERS = ADMINS

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = "US/Eastern"

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = "en-us"

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = os.path.join(PROJECT_ROOT, "media")

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = "/media/"

# Absolute path to the directory that holds static files like app media.
# Example: "/home/media/media.lawrence.com/apps/"
STATIC_ROOT = os.path.join(PROJECT_ROOT, "collected_static")

# URL that handles the static files like app media.
# Example: "http://media.lawrence.com"
STATIC_URL = "/static/"

# Additional directories which hold static files
STATICFILES_DIRS = [
    os.path.join(PROJECT_ROOT, "static"),
]

# Use the default admin media prefix, which is...
#ADMIN_MEDIA_PREFIX = "/static/admin/"

# List of callables that know how to import templates from various sources.
from memcacheify import memcacheify
CACHES = memcacheify()
TEMPLATE_LOADERS = (
        'django.template.loaders.filesystem.Loader',
        'django.template.loaders.app_directories.Loader',
)

MIDDLEWARE_CLASSES = (
    "django.middleware.common.CommonMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "reversion.middleware.RevisionMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "pagination.middleware.PaginationMiddleware",
    "django_sorting.middleware.SortingMiddleware",
)

TEMPLATE_DIRS = [
    os.path.join(PROJECT_ROOT, "templates"),
]

TEMPLATE_CONTEXT_PROCESSORS = [
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.request",
    "django.contrib.messages.context_processors.messages",

    "django.core.context_processors.static",

    "package.context_processors.used_packages_list",
    "grid.context_processors.grid_headers",
    "core.context_processors.current_path",
    "profiles.context_processors.lazy_profile",
    "core.context_processors.core_values",
]

PROJECT_APPS = [
    "grid",
    'core',
    "homepage",
    "package",
    "profiles",
    "apiv1",
    "feeds",
    "searchv2",
]

PREREQ_APPS = [
    # Django
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.sites",
    "django.contrib.messages",
    "django.contrib.humanize",
    "django.contrib.staticfiles",

    # external
    "crispy_forms",
    "pagination",
    "django_extensions",
    "south",
    "tastypie",
    "reversion",
    "django_sorting",
    #"django_modeler",

    'social_auth',
    'floppyforms',
    'rest_framework',

]

INSTALLED_APPS = PREREQ_APPS + PROJECT_APPS


MESSAGE_STORAGE = "django.contrib.messages.storage.session.SessionStorage"

ABSOLUTE_URL_OVERRIDES = {
    "auth.user": lambda o: "/profiles/profile/%s/" % o.username,
}

AUTH_PROFILE_MODULE = "profiles.Profile"

LOGIN_URL = "/login/github/"
LOGIN_REDIRECT_URLNAME = "home"

EMAIL_CONFIRMATION_DAYS = 2
EMAIL_DEBUG = DEBUG

CACHE_TIMEOUT = 60 * 60

ROOT_URLCONF = "urls"

SECRET_KEY = "CHANGEME"

URCHIN_ID = ""

DEFAULT_FROM_EMAIL = 'Django Packages <djangopackages-noreply@djangopackages.com>'
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_SUBJECT_PREFIX = '[Django Packages] '
try:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = 'smtp.sendgrid.net'
    EMAIL_HOST_PASSWORD = os.environ['SENDGRID_PASSWORD']
    EMAIL_HOST_USER = os.environ['SENDGRID_USERNAME']
    EMAIL_PORT = 587
    SERVER_EMAIL = 'info@cartwheelweb.com'
    EMAIL_USE_TLS = True
    DEBUG = False
except Exception as e:
    EMAIL_HOST = 'localhost'
    EMAIL_PORT = 1025

EMAIL_SUBJECT_PREFIX = '[Cartwheel Web]'

DEBUG_TOOLBAR_CONFIG = {
    "INTERCEPT_REDIRECTS": False,
}

PACKAGINATOR_HELP_TEXT = {
    "REPO_URL": "Enter your project repo hosting URL here. Example: https://github.com/opencomparison/opencomparison",
    "PYPI_URL": "<strong>Leave this blank if this package does not have a PyPI release.</strong> What PyPI uses to index your package. Example: django-uni-form",
}

PACKAGINATOR_SEARCH_PREFIX = "django"

# if set to False any auth user can add/modify packages
# only django admins can delete
RESTRICT_PACKAGE_EDITORS = True

# if set to False  any auth user can add/modify grids
# only django admins can delete
RESTRICT_GRID_EDITORS = True


LOCAL_INSTALLED_APPS = []
SUPPORTED_REPO = []

########################## Site specific stuff
FRAMEWORK_TITLE = "Django"
SITE_TITLE = "Django Packages"

if LOCAL_INSTALLED_APPS:
    INSTALLED_APPS.extend(LOCAL_INSTALLED_APPS)

SUPPORTED_REPO.extend(["bitbucket", "github"])


AUTHENTICATION_BACKENDS = (
    'social_auth.backends.contrib.github.GithubBackend',
    'django.contrib.auth.backends.ModelBackend',
)
GITHUB_API_SECRET = environ.get('GITHUB_API_SECRET')
GITHUB_APP_ID = environ.get('GITHUB_APP_ID')
GITHUB_USERNAME = environ.get('GITHUB_USERNAME')
GITHUB_PASSWORD = environ.get('GITHUB_PASSWORD')
SOCIAL_AUTH_ENABLED_BACKENDS = ('github')
SOCIAL_AUTH_COMPLETE_URL_NAME = 'socialauth_complete'
SOCIAL_AUTH_ASSOCIATE_URL_NAME = 'associate_complete'
SOCIAL_AUTH_DEFAULT_USERNAME = lambda u: slugify(u)
SOCIAL_AUTH_EXTRA_DATA = False
SOCIAL_AUTH_CHANGE_SIGNAL_ONLY = True
SOCIAL_AUTH_REDIRECT_IS_HTTPS = True
LOGIN_REDIRECT_URL = '/'

# associate user via email
#SOCIAL_AUTH_ASSOCIATE_BY_MAIL = True

DATABASES = {

    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": "oc",          # Or path to database file if using sqlite3.
        "USER": "",              # Not used with sqlite3.
        "PASSWORD": "",                  # Not used with sqlite3.
        "HOST": "",             # Set to empty string for localhost. Not used with sqlite3.
        "PORT": "",                  # Set to empty string for default. Not used with sqlite3.
    },
}


WSGI_APPLICATION = 'wsgi.application'

if DEBUG:

    MIDDLEWARE_CLASSES += ('debug_toolbar.middleware.DebugToolbarMiddleware',)
    INSTALLED_APPS += ('debug_toolbar',)
    
    INTERNAL_IPS = ('127.0.0.1',)
    
    DEBUG_TOOLBAR_CONFIG = {
        'INTERCEPT_REDIRECTS': False,
        'SHOW_TEMPLATE_CONTEXT': True,
    }
    x = 1

ADMIN_URL_BASE = environ.get('ADMIN_URL_BASE', r"^admin/")

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'standard': {
            'format': "[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s",
            'datefmt': "%d/%b/%Y %H:%M:%S"
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logutils.colorize.ColorizingStreamHandler',
            'formatter': 'standard'
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
            'include_html': True,
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', ],
            'propagate': True,
            'level': 'ERROR',
        },
        'django.request': {

            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': False,
        },
        '': {
            'handlers': ['console', ],
            'level': os.environ.get('DEBUG_LEVEL', 'ERROR'),
        },
    }
}


URL_REGEX_GITHUB = r'(?:http|https|git)://github.com/[^/]*/([^/]*)/{0,1}'

########### redis setup
import redis
from rq import Worker, Queue, Connection

########### end redis setup

########### crispy_forms setup
CRISPY_TEMPLATE_PACK = "bootstrap3"
########### end crispy_forms setup
