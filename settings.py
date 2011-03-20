# -*- coding: utf-8 -*-
# Django settings for basic pinax project.

import os.path
import sys
import posixpath
import pinax

PINAX_ROOT = os.path.abspath(os.path.dirname(pinax.__file__))
PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))

# tells Pinax to use the default theme
PINAX_THEME = "default"

DEBUG = False
TEMPLATE_DEBUG = DEBUG

# tells Pinax to serve media through the staticfiles app.
SERVE_MEDIA = DEBUG

INTERNAL_IPS = [
    "127.0.0.1",
]

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
    os.path.join(PINAX_ROOT, "media", PINAX_THEME),
]

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
# ADMIN_MEDIA_PREFIX = posixpath.join(STATIC_URL, "admin/")
ADMIN_MEDIA_PREFIX = "/site_media/admin/"

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
    "django_openid.consumer.SessionConsumer",
    "django.contrib.messages.middleware.MessageMiddleware",
    "pinax.apps.account.middleware.LocaleMiddleware",
    "pagination.middleware.PaginationMiddleware",
    "django_sorting.middleware.SortingMiddleware",
    "pinax.middleware.security.HideSensistiveFieldsMiddleware",
    "django.contrib.flatpages.middleware.FlatpageFallbackMiddleware",
]

TEMPLATE_DIRS = [
    os.path.join(PROJECT_ROOT, "templates"),
    os.path.join(PINAX_ROOT, "templates", PINAX_THEME),
]

TEMPLATE_CONTEXT_PROCESSORS = [
    "django.core.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.request",
    "django.contrib.messages.context_processors.messages",
    
    "staticfiles.context_processors.static_url",
    
    "pinax.core.context_processors.pinax_settings",
    
    "pinax.apps.account.context_processors.account",
    
    "notification.context_processors.notification",
    "announcements.context_processors.site_wide_announcements",

    "package.context_processors.used_packages_list",
    "homepage.context_processors.grid_tabs",
    "homepage.context_processors.current_path",
]

PROJECT_APPS = [
    "about",
    "grid",
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
    "django.contrib.flatpages",
    
    "pinax.templatetags",
    
    # external
    "notification", # must be first
    "staticfiles",
    "mailer",
    "uni_form",
    "django_openid",
    "ajax_validation",
    "timezones",
    "emailconfirmation",
    "announcements",
    "pagination",
    "idios",
    "django_extensions",
    "south",
    "tastypie",
    "reversion",
    "django_sorting",
    "flatblocks",
    
    # Pinax
    "pinax.apps.account",
    "pinax.apps.signup_codes",
    "pinax.apps.analytics",

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
NOTIFICATION_LANGUAGE_MODULE = "account.Account"

ACCOUNT_OPEN_SIGNUP = True
ACCOUNT_REQUIRED_EMAIL = True
ACCOUNT_EMAIL_VERIFICATION = True
ACCOUNT_EMAIL_AUTHENTICATION = False
ACCOUNT_UNIQUE_EMAIL = EMAIL_CONFIRMATION_UNIQUE_EMAIL = False

AUTHENTICATION_BACKENDS = [
    "pinax.apps.account.auth_backends.AuthenticationBackend",
]

LOGIN_URL = "/account/login/" # @@@ any way this can be a url name?
LOGIN_REDIRECT_URLNAME = "home"

EMAIL_CONFIRMATION_DAYS = 2
EMAIL_DEBUG = DEBUG

ROOT_URLCONF = "packaginator.urls"

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
    "REPO_URL" : "Enter your project repo hosting URL here.<br />Example: https://bitbucket.com/ubernostrum/django-registration",
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

CELERYD_TASK_TIME_LIMIT = 300
LAUNCHPAD_ACTIVE = False

LOCAL_INSTALLED_APPS = []
SUPPORTED_REPO = []

# local_settings.py can be used to override environment-specific settings
# like database and email that differ between development and production.
try:
    from local_settings import *
except ImportError:
    pass

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
