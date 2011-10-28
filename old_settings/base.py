# -*- coding: utf-8 -*-
# Django settings for basic pinax project.

import os.path
import sys
import posixpath

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir))
sys.path.append(os.path.join(PROJECT_ROOT, 'apps')) # ensure we can find the apps

DEBUG = False
TEMPLATE_DEBUG = DEBUG

# serve media through the staticfiles app.
SERVE_MEDIA = DEBUG

ADMINS = [
    # ("Your Name", "your_email@domain.com"),
]

MANAGERS = ADMINS

DATABASES = {
    "default": {
        "ENGINE": "", # Add "postgresql_psycopg2", "postgresql", "mysql", "sqlite3" or "oracle".
        "NAME": "",                       # Or path to database file if using sqlite3.
        "USER": "",                             # Not used with sqlite3.
        "PASSWORD": "",                         # Not used with sqlite3.
        "HOST": "",                             # Set to empty string for localhost. Not used with sqlite3.
        "PORT": "",                             # Set to empty string for default. Not used with sqlite3.
    }
}

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
MEDIA_ROOT = os.path.join(PROJECT_ROOT, "site_media", "media")

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = "/site_media/media/"

# Absolute path to the directory that holds static files like app media.
# Example: "/home/media/media.lawrence.com/apps/"
STATIC_ROOT = os.path.join(PROJECT_ROOT, "site_media", "static")

# URL that handles the static files like app media.
# Example: "http://media.lawrence.com"
STATIC_URL = "/site_media/static/"

# Additional directories which hold static files
STATICFILES_DIRS = [
    os.path.join(PROJECT_ROOT, "media"),
]

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = posixpath.join(STATIC_URL, "admin/")

# List of callables that know how to import templates from various sources.
if DEBUG:
    CACHE_BACKEND = 'dummy://'
    TEMPLATE_LOADERS = (
            'django.template.loaders.filesystem.Loader',
            'django.template.loaders.app_directories.Loader',
    )
else:
    CACHE_BACKEND = 'dummy://'
    TEMPLATE_LOADERS = (
            'django.template.loaders.filesystem.Loader',
            'django.template.loaders.app_directories.Loader',
    )

MIDDLEWARE_CLASSES = [
    "django.middleware.common.CommonMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "reversion.middleware.RevisionMiddleware",    
    "django.contrib.messages.middleware.MessageMiddleware",
    "pagination.middleware.PaginationMiddleware",
    "django_sorting.middleware.SortingMiddleware",
]

TEMPLATE_DIRS = [
    os.path.join(PROJECT_ROOT, "templates"),
]

TEMPLATE_CONTEXT_PROCESSORS = [
    "django.core.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.request",
    "django.core.context_processors.static",
    "django.contrib.messages.context_processors.messages",
    
    "notification.context_processors.notification",

    "package.context_processors.used_packages_list",
    "homepage.context_processors.grid_tabs",
    "homepage.context_processors.current_path",
    "profiles.context_processors.lazy_profile",
]

PROJECT_APPS = [
    "about",
    "grid",
    'core',
    "homepage",
    "package",
    "profiles",
    "searchv1",
    "apiv1",
    "feeds",
    "pypi",
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
    "notification", # must be first
    "uni_form",
    "pagination",
    "django_extensions",
    "south",
    "tastypie",
    "reversion",
    "django_sorting",
    "django_modeler",
    
    # Celery task queue:
    'djcelery',
    
]

INSTALLED_APPS = PREREQ_APPS + PROJECT_APPS

FIXTURE_DIRS = [
    os.path.join(PROJECT_ROOT, "fixtures"),
]

MESSAGE_STORAGE = "django.contrib.messages.storage.session.SessionStorage"

ABSOLUTE_URL_OVERRIDES = {
    "auth.user": lambda o: "/profiles/profile/%s/" % o.username,
}

AUTH_PROFILE_MODULE = "profiles.Profile"

ACCOUNT_OPEN_SIGNUP = True
ACCOUNT_REQUIRED_EMAIL = True
ACCOUNT_EMAIL_VERIFICATION = True
ACCOUNT_EMAIL_AUTHENTICATION = False
ACCOUNT_UNIQUE_EMAIL = EMAIL_CONFIRMATION_UNIQUE_EMAIL = False
ACCOUNT_ACTIVATION_DAYS = 7

LOGIN_URL = "/login/"
LOGIN_REDIRECT_URLNAME = "home"

EMAIL_CONFIRMATION_DAYS = 2
EMAIL_DEBUG = DEBUG

CACHE_TIMEOUT = 60 * 60

ROOT_URLCONF = "opencomparison.urls"

SECRET_KEY = "ud%a+c#@@d5k!t_)mpw!+58fztyhk_sq%c5s0p5_je-wixy#$k"

URCHIN_ID = ""

DEFAULT_FROM_EMAIL = 'Django Packages <djangopackages-noreply@djangopackages.com>'
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_USE_TLS = True
EMAIL_HOST = 'localhost'
EMAIL_HOST_USER = 'djangopackages-noreply@djangopackages.com'
EMAIL_HOST_PASSWORD = ''
EMAIL_PORT = 25
EMAIL_SUBJECT_PREFIX = '[Django Packages] '

DEBUG_TOOLBAR_CONFIG = {
    "INTERCEPT_REDIRECTS": False,
}

if DEBUG:
    CACHE_BACKEND = 'dummy://'
    TEMPLATE_LOADERS = (
            'django.template.loaders.filesystem.Loader',
            'django.template.loaders.app_directories.Loader',
    )

#TEST_RUNNER = 'testrunner.OurTestRunner'
TEST_RUNNER = 'testrunner.OurCoverageRunner'

COVERAGE_MODULE_EXCLUDES = [
    'tests$', 'settings$', 'urls$', 'locale$',
    'migrations', 'fixtures',
]
COVERAGE_MODULE_EXCLUDES += PREREQ_APPS + ["djkombu",]
COVERAGE_REPORT_HTML_OUTPUT_DIR = "coverage"

PACKAGINATOR_HELP_TEXT = {
    "REPO_URL" : "Enter your project repo hosting URL here.<br />Example: https://bitbucket.org/ubernostrum/django-registration",
    "PYPI_URL" : "<strong>Leave this blank if this package does not have a PyPI release.</strong><br />What PyPI uses to index your package. <br />Example: django-registration",
    "CATEGORY" : """
    <ul>
     <li><strong>Apps</strong> is anything that is installed by placing in settings.INSTALLED_APPS.</li>
     <li><strong>Frameworks</strong> are large efforts that combine many python modules or apps to build things like Pinax.</li>
     <li><strong>Other</strong> are not installed by settings.INSTALLED_APPS, are not frameworks or sites but still help Django in some way.</li>
     <li><strong>Projects</strong> are individual projects such as Django Packages, DjangoProject.com, and others.</li>
    </ul>
"""
}

PACKAGINATOR_SEARCH_PREFIX = "django"

# if set to False any auth user can add/modify packages
# only django admins can delete
RESTRICT_PACKAGE_EDITORS = True

# if set to False  any auth user can add/modify grids
# only django admins can delete
RESTRICT_GRID_EDITORS = True

# package extenders are dicts that can include:
    # form
    # model
    # grid_items
    # package_displays
PACKAGE_EXTENDERS = []


CELERYD_TASK_TIME_LIMIT = 300
LAUNCHPAD_ACTIVE = False

LOCAL_INSTALLED_APPS = []
SUPPORTED_REPO = []

# accounts settings
ACCOUNTS_ACTIVATION_EMAIL = True
if DEBUG:
    ACCOUNTS_ACTIVATION_EMAIL = False

if LOCAL_INSTALLED_APPS:
    INSTALLED_APPS.extend(LOCAL_INSTALLED_APPS)

SUPPORTED_REPO.extend(["bitbucket", "github"])
if LAUNCHPAD_ACTIVE:
    SUPPORTED_REPO += ["launchpad"]

try:
    import djcelery

    djcelery.setup_loader()
except ImportError:
    # skipping this so we can generate docs
    # Doing this cause most development doesn't need it.
    pass
