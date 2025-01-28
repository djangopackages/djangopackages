# Django settings
import os.path
import sys
from pathlib import Path

import environ
import sentry_sdk
import structlog
from django.template.defaultfilters import slugify
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.redis import RedisIntegration

from core import __version__

env = environ.Env()

BASE_DIR = Path(__file__).parent

PROJECT_ROOT = Path(__file__).parent

DEBUG = env.bool("DJANGO_DEBUG", True)
TEMPLATE_DEBUG = env.bool("TEMPLATE_DEBUG", True)
TEST_MODE = "pytest" in sys.modules

########## CACHE
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": env.str("REDIS_URL"),
    }
}


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

USE_TZ = False

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
if DEBUG:
    MEDIA_ROOT = PROJECT_ROOT.joinpath("media")
else:
    MEDIA_ROOT = "/data/media"

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = "/media/"

# Absolute path to the directory that holds static files like app media.
# Example: "/home/media/media.lawrence.com/apps/"
if DEBUG:
    STATIC_ROOT = PROJECT_ROOT.joinpath("collected_static")
else:
    STATIC_ROOT = os.path.join(PROJECT_ROOT, "collected_static")

# URL that handles the static files like app media.
# Example: "http://media.lawrence.com"
STATIC_URL = "/static/"

# Additional directories which hold static files
STATICFILES_DIRS = [
    PROJECT_ROOT.joinpath("static"),
]

HEALTHCHECK = env.bool("HEALTHCHECK", False)
PACKAGE_HEALTHCHECK_URL = env.str("PACKAGE_HEALTHCHECK_URL", "")
PYPI_HEALTHCHECK_URL = env.str("PYPI_HEALTHCHECK_URL", "")
SEARCHV2_HEALTHCHECK_URL = env.str("SEARCHV2_HEALTHCHECK_URL", "")

# Configure Redis
REDIS_HOST = env("REDIS_HOST", default="redis")

# Configure Celery
CELERY_BROKER_URL = f"redis://{REDIS_HOST}:6379"
CELERY_RESULT_BACKEND = f"redis://{REDIS_HOST}:6379"
CELERY_ACCEPT_CONTENT = ["application/json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "UTC"


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
                "core.context_processors.settings_context",
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
    "blog",
    "classifiers",
    "core",
    "favorites",
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
    "django.contrib.sitemaps",
    "django.contrib.sites",
    "django.contrib.messages",
    "django.contrib.humanize",
    "django.contrib.staticfiles",
    # external
    "maintenance_mode",
    "crispy_bootstrap3",
    "crispy_forms",
    "django_better_admin_arrayfield",
    "django_extensions",
    "django_htmx",
    "django_tables2",
    "django_tailwind_cli",
    "heroicons",
    "emojificate",
    "rest_framework",
    "reversion",
    "social_django",
    "waffle",
    "django_q",
    "template_partials",
    "anymail",
]

INSTALLED_APPS = PREREQ_APPS + PROJECT_APPS

ANYMAIL = {
    "MAILGUN_API_KEY": env.str("MAILGUN_API_KEY", "mail-gun-api-key"),
    "MAILGUN_SENDER_DOMAIN": env.str("MAILGUN_SENDER_DOMAIN", "mail-gun-sender-domain"),
}


# Set the default scheme for forms.URLField to "https"
# TODO: Remove transitional setting in Django 6.0
FORMS_URLFIELD_ASSUME_HTTPS = True

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

SECRET_KEY = env("SECRET_KEY", default="CHANGEME")

URCHIN_ID = ""

DEFAULT_FROM_EMAIL = "Django Packages <djangopackages-noreply@djangopackages.org>"

if DEBUG:
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_SUBJECT_PREFIX = "[Django Packages] "
else:
    EMAIL_BACKEND = "anymail.backends.mailgun.MailgunBackend"
    EMAIL_SUBJECT_PREFIX = env("EMAIL_SUBJECT_PREFIX", default="[Django Packages] ")

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
if DEBUG:
    RESTRICT_GRID_EDITORS = True
else:
    RESTRICT_GRID_EDITORS = False

# Sentry Configuration

if SENTRY_DSN := env("DJANGO_SENTRY_DSN", default=None):
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[DjangoIntegration(), RedisIntegration()],
        release=f"{__version__}",
        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for performance monitoring.
        # We recommend adjusting this value in production.
        traces_sample_rate=0.2,
        # Set profiles_sample_rate to 1.0 to profile 100%
        # of sampled transactions.
        # This setting is relative to the traces_sample_rate setting.
        profiles_sample_rate=0.8,
        # If you wish to associate users to errors (assuming you are using
        # django.contrib.auth) you may enable sending PII data.
        send_default_pii=True,
    )


LOCAL_INSTALLED_APPS = []

########################## Site specific stuff
FRAMEWORK_TITLE = env("FRAMEWORK_TITLE", default="Django")
SITE_TITLE = env("SITE_TITLE", default="Django Packages")

PACKAGE_SCORE_MIN = env.int("PACKAGE_SCORE_MIN", default=-500)

if LOCAL_INSTALLED_APPS:
    INSTALLED_APPS.extend(LOCAL_INSTALLED_APPS)

SUPPORTED_REPO = ["bitbucket", "github", "gitlab", "codeberg"]

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


########## DATABASE CONFIGURATION
# ------------------------------------------------------------------------------
# Raises ImproperlyConfigured exception if DATABASE_URL not in os.environ
DATABASES = {"default": env.db("DATABASE_URL")}
DATABASES["default"] = env.db("DATABASE_URL")
DATABASES["default"]["DISABLE_SERVER_SIDE_CURSORS"] = True
DATABASES["default"]["CONN_HEALTH_CHECKS"] = True
DATABASES["default"]["OPTIONS"] = {
    "pool": {
        "min_size": 2,
        "max_size": 10,
        "timeout": 10,
    }
}

########## END DATABASE CONFIGURATION


DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

WSGI_APPLICATION = "wsgi.application"

if DEBUG and not TEST_MODE:
    INSTALLED_APPS += ["debug_toolbar"]
    MIDDLEWARE.append("debug_toolbar.middleware.DebugToolbarMiddleware")
    DEBUG_TOOLBAR_CONFIG = {
        "INTERCEPT_REDIRECTS": False,
        "SHOW_TOOLBAR_CALLBACK": lambda _request: DEBUG,
    }

########## django-secure

# TODO: remove django-secure
if not DEBUG:
    INSTALLED_APPS += [
        "djangosecure",
    ]

    # set this to 60 seconds and then to 518400 when you can prove it works
    SECURE_HSTS_SECONDS = 60
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_FRAME_DENY = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_BROWSER_XSS_FILTER = True
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True

    # TODO: Change this to True when we get closer to real deployment
    SECURE_SSL_REDIRECT = False

    ########## end django-secure


ADMIN_URL_BASE = env("ADMIN_URL_BASE", default="admin/")

if not DEBUG:
    LOGGING = {
        "version": 1,
        "disable_existing_loggers": True,
        "root": {
            "level": "WARNING",
            "handlers": ["console"],
        },
        "formatters": {
            "json_formatter": {
                "()": structlog.stdlib.ProcessorFormatter,
                "processor": structlog.processors.JSONRenderer(),
            },
            "plain_console": {
                "()": structlog.stdlib.ProcessorFormatter,
                "processor": structlog.dev.ConsoleRenderer(),
            },
            "key_value": {
                "()": structlog.stdlib.ProcessorFormatter,
                "processor": structlog.processors.KeyValueRenderer(
                    key_order=["timestamp", "level", "event", "logger"]
                ),
            },
            "verbose": {
                "format": "%(levelname)s %(asctime)s %(module)s "
                "%(process)d %(thread)d %(message)s"
            },
        },
        "handlers": {
            "console": {
                "level": "DEBUG",
                "class": "logging.StreamHandler",
                "formatter": "plain_console",
            },
        },
        "loggers": {
            "django.db.backends": {
                "level": "ERROR",
                "handlers": ["console"],
                "propagate": True,
            },
            "django_structlog": {
                "handlers": ["console"],
                "level": "INFO",
                "propagate": False,
            },
        },
    }

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.filter_by_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


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
WAFFLE_CREATE_MISSING_FLAGS = True

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

TAILWIND_CLI_AUTOMATIC_DOWNLOAD = False
TAILWIND_CLI_CONFIG_FILE = "tailwind.config.js"
TAILWIND_CLI_DIST_CSS = "css/tailwind.css"
TAILWIND_CLI_SRC_CSS = "tailwindcss.css"
TAILWIND_CLI_VERSION = "3.4.3"
