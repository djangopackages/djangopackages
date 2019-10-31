# -*- coding: utf-8 -*-
"""Docker specific settings.
"""

import logging

from .base import *


########## CACHE
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": env.str('REDIS_URL'),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "IGNORE_EXCEPTIONS": True,  # mimics memcache behavior.
                                        # http://niwinz.github.io/django-redis/latest/#_memcached_exceptions_behavior
        }
    }
}


# Anymail with Mailgun
INSTALLED_APPS += ("anymail", )
ANYMAIL = {
    "MAILGUN_API_KEY": env('DJANGO_MAILGUN_API_KEY'),
    "MAILGUN_SENDER_DOMAIN": env('MAILGUN_SENDER_DOMAIN')
}
EMAIL_BACKEND = "anymail.backends.mailgun.MailgunBackend"
EMAIL_SUBJECT_PREFIX = environ.get('EMAIL_SUBJECT_PREFIX', '[Django Packages] ')


########## SECRET
SECRET_KEY = environ.get('SECRET_KEY', '')


########## SITE
SITE_TITLE = environ.get('SITE_TITLE')
FRAMEWORK_TITLE = environ.get('FRAMEWORK_TITLE')





########### Permissions
RESTRICT_PACKAGE_EDITORS = False
RESTRICT_GRID_EDITORS = False

# Sentry Configuration
INSTALLED_APPS += ('raven.contrib.django.raven_compat', )
RAVEN_MIDDLEWARE = ['raven.contrib.django.raven_compat.middleware.SentryResponseErrorIdMiddleware']
MIDDLEWARE = RAVEN_MIDDLEWARE + MIDDLEWARE
SENTRY_DSN = env('DJANGO_SENTRY_DSN')
SENTRY_CLIENT = env('DJANGO_SENTRY_CLIENT', default='raven.contrib.django.raven_compat.DjangoClient')
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'root': {
        'level': 'WARNING',
        'handlers': ['sentry'],
    },
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s '
                      '%(process)d %(thread)d %(message)s'
        },
    },
    'handlers': {
        'sentry': {
            'level': 'ERROR',
            'class': 'raven.contrib.django.raven_compat.handlers.SentryHandler',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        }
    },
    'loggers': {
        'django.db.backends': {
            'level': 'ERROR',
            'handlers': ['console'],
            'propagate': False,
        },
        'raven': {
            'level': 'DEBUG',
            'handlers': ['console'],
            'propagate': False,
        },
        'sentry.errors': {
            'level': 'DEBUG',
            'handlers': ['console'],
            'propagate': False,
        },
        'django.security.DisallowedHost': {
            'level': 'ERROR',
            'handlers': ['console', 'sentry'],
            'propagate': False,
        },
    },
}
SENTRY_CELERY_LOGLEVEL = env.int('DJANGO_SENTRY_LOG_LEVEL', logging.INFO)
RAVEN_CONFIG = {
    'CELERY_LOGLEVEL': env.int('DJANGO_SENTRY_LOG_LEVEL', logging.INFO),
    'DSN': SENTRY_DSN
}


########## DATABASE CONFIGURATION
# ------------------------------------------------------------------------------
# Raises ImproperlyConfigured exception if DATABASE_URL not in os.environ
DATABASES['default'] = env.db("DATABASE_URL")
########## END DATABASE CONFIGURATION

########## django-secure

INSTALLED_APPS += ["djangosecure", ]
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
TEMPLATES[0]['OPTIONS']['loaders'] = [
('django.template.loaders.cached.Loader', (
        'django.template.loaders.filesystem.Loader',
        'django.template.loaders.app_directories.Loader',
    )),
]

########## end templates

# Static Assets
# ------------------------
MEDIA_ROOT = "/data/media"
STATIC_ROOT = "/data/static"

HEALTHCHECK = env.bool("HEALTHCHECK", False)
PACKAGE_HEALTHCHECK_URL = env.str("PACKAGE_HEALTHCHECK_URL", "")
PYPI_HEALTHCHECK_URL = env.str("PYPI_HEALTHCHECK_URL", "")
SEARCHV2_HEALTHCHECK_URL = env.str("SEARCHV2_HEALTHCHECK_URL", "")
