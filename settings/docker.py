"""Docker specific settings.
"""
import os.path

import sentry_sdk
import structlog
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.redis import RedisIntegration

from core import __version__

from .base import *

DEBUG = env.bool("DJANGO_DEBUG", False)

########## CACHE
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": env.str("REDIS_URL"),
    }
}


# Anymail with Mailgun
INSTALLED_APPS += ("anymail",)
ANYMAIL = {
    "MAILGUN_API_KEY": env("MAILGUN_API_KEY"),
    "MAILGUN_SENDER_DOMAIN": env("MAILGUN_SENDER_DOMAIN"),
}
EMAIL_BACKEND = "anymail.backends.mailgun.MailgunBackend"
EMAIL_SUBJECT_PREFIX = env("EMAIL_SUBJECT_PREFIX", default="[Django Packages] ")


########## SECRET
SECRET_KEY = env("SECRET_KEY", default="")


########## SITE
SITE_TITLE = env("SITE_TITLE")
FRAMEWORK_TITLE = env("FRAMEWORK_TITLE")


########### Permissions
RESTRICT_PACKAGE_EDITORS = False
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
        # "django": {
        #     # "handlers": ["console"],
        #     "propagate": True,
        # },
        # "django.request": {
        #     "level": "DEBUG",
        #     "handlers": ["console"],
        #     "propagate": True,
        # },
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


########## DATABASE CONFIGURATION
# ------------------------------------------------------------------------------
# Raises ImproperlyConfigured exception if DATABASE_URL not in os.environ
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

########## django-secure

INSTALLED_APPS += [
    "djangosecure",
]
# todo: remove django-secure
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


########## templates
# TEMPLATES[0]["OPTIONS"]["loaders"] = [
#     (
#         "django.template.loaders.cached.Loader",
#         (
#             "django.template.loaders.filesystem.Loader",
#             "django.template.loaders.app_directories.Loader",
#         ),
#     ),
# ]

########## end templates

# Static Assets
# ------------------------
MEDIA_ROOT = "/data/media"
STATIC_ROOT = os.path.join(PROJECT_ROOT, "collected_static")
STATICFILES_DIRS = [
    PROJECT_ROOT.joinpath("static"),
    # "/data/static",
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
