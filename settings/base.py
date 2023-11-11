# Django settings
import sys
from pathlib import Path

import environ
from django.template.defaultfilters import slugify

env = environ.Env()

PROJECT_ROOT = Path(__file__).parent.parent

DEBUG = env.bool("DJANGO_DEBUG", True)
TEMPLATE_DEBUG = env.bool("TEMPLATE_DEBUG", True)
TEST_MODE = "pytest" in sys.modules

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
MEDIA_ROOT = PROJECT_ROOT.joinpath("media")

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = "/media/"

# Absolute path to the directory that holds static files like app media.
# Example: "/home/media/media.lawrence.com/apps/"
STATIC_ROOT = PROJECT_ROOT.joinpath("collected_static")

# URL that handles the static files like app media.
# Example: "http://media.lawrence.com"
STATIC_URL = "/static/"

# Additional directories which hold static files
STATICFILES_DIRS = [
    PROJECT_ROOT.joinpath("static"),
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
    "django_htmx.middleware.HtmxMiddleware",
    "waffle.middleware.WaffleMiddleware",
    "django_structlog.middlewares.RequestMiddleware",
    "maintenance_mode.middleware.MaintenanceModeMiddleware",
]

TEMPLATES = [
    {
        "APP_DIRS": True,
        # See: https://docs.djangoproject.com/en/dev/ref/settings/#std:setting-TEMPLATES-BACKEND
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        # See: https://docs.djangoproject.com/en/dev/ref/settings/#template-dirs
        "DIRS": [
            PROJECT_ROOT.joinpath("templates"),
        ],
        "OPTIONS": {
            # See: https://docs.djangoproject.com/en/dev/ref/settings/#template-debug
            "debug": TEMPLATE_DEBUG,
            # See: https://docs.djangoproject.com/en/dev/ref/settings/#template-loaders
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
    "apiv3",
    "classifiers",
    "core",
    # "commands",
    "feeds",
    "homepage",
    "package",
    "products",
    "profiles",
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
    "maintenance_mode",
    "crispy_forms",
    "crispy_bootstrap3",
    "django_better_admin_arrayfield",
    "django_extensions",
    "django_htmx",
    "django_tables2",
    "emojificate",
    "rest_framework",
    "reversion",
    "social_django",
    "waffle",
    "django_q",
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
SERVER_EMAIL = "info@djangopackages.org"


EMAIL_SUBJECT_PREFIX = "[Django Packages]"

PACKAGINATOR_HELP_TEXT = {
    "REPO_URL": "Enter your project repo hosting URL here. Example: https://github.com/djangopackages/djangopackages",
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

# GitLab settings
GITLAB_TOKEN = env("GITLAB_TOKEN", default="")

# GitHub settings
GITHUB_API_SECRET = env("GITHUB_API_SECRET", default="")
GITHUB_APP_ID = env("GITHUB_APP_ID", default="")
GITHUB_TOKEN = env("GITHUB_TOKEN", default="")

# GitHub OAuth for login settings
SOCIAL_AUTH_ASSOCIATE_URL_NAME = "associate_complete"
SOCIAL_AUTH_COMPLETE_URL_NAME = "socialauth_complete"
SOCIAL_AUTH_ENABLED_BACKENDS = ("github",)
SOCIAL_AUTH_GITHUB_KEY = env("SOCIAL_AUTH_GITHUB_KEY", default=GITHUB_APP_ID)
SOCIAL_AUTH_GITHUB_SECRET = env("SOCIAL_AUTH_GITHUB_SECRET", default=GITHUB_API_SECRET)


def SOCIAL_AUTH_DEFAULT_USERNAME(u):
    return slugify(u)


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

if DEBUG and not TEST_MODE:
    INSTALLED_APPS += ["debug_toolbar"]
    MIDDLEWARE.append("debug_toolbar.middleware.DebugToolbarMiddleware")
    DEBUG_TOOLBAR_CONFIG = {
        "INTERCEPT_REDIRECTS": False,
        "SHOW_TOOLBAR_CALLBACK": lambda _request: DEBUG,
    }

ADMIN_URL_BASE = env("ADMIN_URL_BASE", default="admin/")

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
#             'level': os.env('DEBUG_LEVEL', 'ERROR'),
#         },
#     }
# }


URL_REGEX_GITHUB = r"(?:http|https|git)://github.com/[^/]*/([^/]*)/{0,1}"

########### redis setup

# import redis
# from rq import Worker, Queue, Connection

########### end redis setup

########### crispy_forms setup
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap3"
CRISPY_TEMPLATE_PACK = "bootstrap3"
########### end crispy_forms setup

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
FORM_RENDERER = "django.forms.renderers.DjangoDivFormRenderer"

# django-q2 settings
# https://django-q2.readthedocs.io/en/stable/configure.html
Q_CLUSTER = {
    "name": "djangopackages",
    "redis": env.str("REDIS_URL"),
    "timeout": 600,  # this won't work for longer running tasks that might take hours to run
    "retry": 700,
    "max_attempts": 2,
    "workers": 4,
}

if DEBUG:
    DOCS_URL = "http://0.0.0.0:4000"
else:
    DOCS_URL = "https://docs.djangopackages.org"
