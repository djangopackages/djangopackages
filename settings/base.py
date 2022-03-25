# Django settings

import os.path
from os import environ
import environ as envmax

from django.template.defaultfilters import slugify

env = envmax.Env()

PROJECT_ROOT = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

DEBUG = env.bool("DJANGO_DEBUG", True)
TEMPLATE_DEBUG = env.bool("TEMPLATE_DEBUG", True)

INTERNAL_IPS = [
    "127.0.0.1",
]

ADMINS = [
    ("Django Packages", "info@djangopackages.org"),
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

# RemovedInDjango50Warning: The default value of USE_TZ will change from
# False to True in Django 5.0. Set USE_TZ to False in your project
# settings if you want to keep the current default behavior.
USE_TZ = False

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
# ADMIN_MEDIA_PREFIX = "/static/admin/"


MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "dj_pagination.middleware.PaginationMiddleware",
    "waffle.middleware.WaffleMiddleware",
    "django_structlog.middlewares.RequestMiddleware",
    "maintenance_mode.middleware.MaintenanceModeMiddleware",
]

TEMPLATES = [
    {
        # See: https://docs.djangoproject.com/en/dev/ref/settings/#std:setting-TEMPLATES-BACKEND
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        # See: https://docs.djangoproject.com/en/dev/ref/settings/#template-dirs
        "DIRS": [
            os.path.join(PROJECT_ROOT, "templates"),
        ],
        "OPTIONS": {
            # See: https://docs.djangoproject.com/en/dev/ref/settings/#template-debug
            "debug": TEMPLATE_DEBUG,
            # See: https://docs.djangoproject.com/en/dev/ref/settings/#template-loaders
            # https://docs.djangoproject.com/en/dev/ref/templates/api/#loader-types
            "loaders": [
                "django.template.loaders.filesystem.Loader",
                "django.template.loaders.app_directories.Loader",
            ],
            # See: https://docs.djangoproject.com/en/dev/ref/settings/#template-context-processors
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.template.context_processors.i18n",
                "django.template.context_processors.media",
                "django.template.context_processors.static",
                "django.template.context_processors.tz",
                "django.contrib.messages.context_processors.messages",
                # Your stuff: custom template context processors go here
                "maintenance_mode.context_processors.maintenance_mode",
                "package.context_processors.used_packages_list",
                "grid.context_processors.grid_headers",
                "core.context_processors.current_path",
                "profiles.context_processors.lazy_profile",
                "social_django.context_processors.backends",
                "social_django.context_processors.login_redirect",
                "core.context_processors.core_values",
            ],
        },
    },
]

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
]

PROJECT_APPS = [
    "grid",
    "core",
    "homepage",
    "package",
    "profiles",
    "feeds",
    "searchv2",
    "apiv3",
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
    "maintenance_mode",
    "crispy_forms",
    "dj_pagination",
    "django_better_admin_arrayfield",
    "django_extensions",
    "django_tables2",
    "rest_framework",
    "reversion",
    "social_django",
    "waffle",
    "webstack_django_sorting",
]

INSTALLED_APPS = PREREQ_APPS + PROJECT_APPS


MESSAGE_STORAGE = "django.contrib.messages.storage.session.SessionStorage"

ABSOLUTE_URL_OVERRIDES = {
    "auth.user": lambda o: "/profiles/%s/" % o.username,
}

AUTH_PROFILE_MODULE = "profiles.Profile"

LOGIN_URL = "/auth/login/github/"
LOGIN_REDIRECT_URLNAME = "home"
LOGOUT_REDIRECT_URL = "/"

EMAIL_CONFIRMATION_DAYS = 2
EMAIL_DEBUG = DEBUG

CACHE_TIMEOUT = 60 * 60

ROOT_URLCONF = "urls"

SECRET_KEY = "CHANGEME"

URCHIN_ID = ""

DEFAULT_FROM_EMAIL = "Django Packages <djangopackages-noreply@djangopackages.org>"
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_SUBJECT_PREFIX = "[Django Packages] "
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
SERVER_EMAIL = "info@djangopackages.org"

try:
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_HOST = "smtp.sendgrid.net"
    EMAIL_HOST_PASSWORD = SENDGRID_API_KEY
    EMAIL_HOST_USER = "apikey"
    EMAIL_PORT = 587
    EMAIL_USE_TLS = True
    EMAIL_USE_TLS = True
except Exception:
    EMAIL_HOST = "localhost"
    EMAIL_PORT = 1025

EMAIL_SUBJECT_PREFIX = "[Django Packages]"

PACKAGINATOR_HELP_TEXT = {
    "REPO_URL": "Enter your project repo hosting URL here. Example: https://github.com/djangopackages/opencomparison",
    "PYPI_URL": "<strong>Leave this blank if this package does not have a PyPI release.</strong> What PyPI uses to index your package. Example: django-uni-form",
}

PACKAGINATOR_SEARCH_PREFIX = "django"

# if set to False any auth user can add/modify packages
# only django admins can delete
RESTRICT_PACKAGE_EDITORS = False

# if set to False  any auth user can add/modify grids
# only django admins can delete
RESTRICT_GRID_EDITORS = True


LOCAL_INSTALLED_APPS = []
SUPPORTED_REPO = []

########################## Site specific stuff
FRAMEWORK_TITLE = "Django"
SITE_TITLE = "Django Packages"

PACKAGE_SCORE_MIN = env.int("PACKAGE_SCORE_MIN", default=-500)

if LOCAL_INSTALLED_APPS:
    INSTALLED_APPS.extend(LOCAL_INSTALLED_APPS)

# SUPPORTED_REPO.extend(["bitbucket", "github", "gitlab"])
SUPPORTED_REPO.extend(["bitbucket", "github"])


AUTHENTICATION_BACKENDS = (
    "social_core.backends.github.GithubOAuth2",
    "django.contrib.auth.backends.ModelBackend",
)
GITHUB_API_SECRET = environ.get("GITHUB_API_SECRET")
GITHUB_APP_ID = environ.get("GITHUB_APP_ID")
GITHUB_USERNAME = environ.get("GITHUB_USERNAME")
SOCIAL_AUTH_GITHUB_KEY = GITHUB_APP_ID
SOCIAL_AUTH_GITHUB_SECRET = GITHUB_API_SECRET
SOCIAL_AUTH_ENABLED_BACKENDS = ("github",)
SOCIAL_AUTH_COMPLETE_URL_NAME = "socialauth_complete"
SOCIAL_AUTH_ASSOCIATE_URL_NAME = "associate_complete"
SOCIAL_AUTH_DEFAULT_USERNAME = lambda u: slugify(u)
SOCIAL_AUTH_GITHUB_EXTRA_DATA = []
SOCIAL_AUTH_CHANGE_SIGNAL_ONLY = True
SOCIAL_AUTH_REDIRECT_IS_HTTPS = False
SOCIAL_AUTH_ADMIN_USER_SEARCH_FIELDS = ["username", "first_name", "email"]
LOGIN_REDIRECT_URL = "/"

# associate user via email
# SOCIAL_AUTH_ASSOCIATE_BY_MAIL = True

DATABASES = {"default": env.db("DATABASE_URL")}

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"


WSGI_APPLICATION = "wsgi.application"

if DEBUG:
    INSTALLED_APPS += ["debug_toolbar"]
    # MIDDLEWARE.append("debug_toolbar.middleware.DebugToolbarMiddleware")
    DEBUG_TOOLBAR_CONFIG = {
        "INTERCEPT_REDIRECTS": False,
        "SHOW_TOOLBAR_CALLBACK": lambda _request: DEBUG,
    }

ADMIN_URL_BASE = environ.get("ADMIN_URL_BASE", r"^admin/")

# LOGGING = {
#     'version': 1,
#     'disable_existing_loggers': True,
#     'formatters': {
#         'standard': {
#             'format': "[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s",
#             'datefmt': "%d/%b/%Y %H:%M:%S"
#         },
#     },
#     'handlers': {
#         'console': {
#             'level': 'DEBUG',
#             'class': 'logutils.colorize.ColorizingStreamHandler',
#             'formatter': 'standard'
#         },
#         'mail_admins': {
#             'level': 'ERROR',
#             'class': 'django.utils.log.AdminEmailHandler',
#             'include_html': True,
#         },
#     },
#     'loggers': {
#         'django': {
#             'handlers': ['console', ],
#             'propagate': True,
#             'level': 'ERROR',
#         },
#         'django.request': {

#             'handlers': ['mail_admins'],
#             'level': 'ERROR',
#             'propagate': False,
#         },
#         '': {
#             'handlers': ['console', ],
#             'level': os.environ.get('DEBUG_LEVEL', 'ERROR'),
#         },
#     }
# }


URL_REGEX_GITHUB = r"(?:http|https|git)://github.com/[^/]*/([^/]*)/{0,1}"

########### redis setup

# import redis
# from rq import Worker, Queue, Connection

########### end redis setup

########### crispy_forms setup
CRISPY_TEMPLATE_PACK = "bootstrap3"
########### end crispy_forms setup


########## GITHUB
GITHUB_API_SECRET = environ.get("GITHUB_API_SECRET")
GITHUB_APP_ID = environ.get("GITHUB_APP_ID")
GITHUB_TOKEN = environ.get("GITHUB_TOKEN")

GITLAB_TOKEN = environ.get("GITLAB_TOKEN", "")

########### SEKURITY
ALLOWED_HOSTS = ["*"]

REST_FRAMEWORK = {
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.LimitOffsetPagination",
    "PAGE_SIZE": 20,
}

WAFFLE_CREATE_MISSING_SWITCHES = True

# django-maintenance-mode settings
MAINTENANCE_MODE = None

# alternatively it is possible to use the default storage backend
MAINTENANCE_MODE_STATE_BACKEND = "maintenance_mode.backends.DefaultStorageBackend"

# if True admin site will not be affected by the maintenance-mode page
MAINTENANCE_MODE_IGNORE_ADMIN_SITE = True
