# -*- coding: utf-8 -*-
"""Docker specific settings.
"""

from os import environ
import environ as envmax

env = envmax.Env()

from .base import *


########## CACHE
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "{0}/{1}".format(env.cache_url('REDIS_URL', default="redis://127.0.0.1:6379"), 0),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "IGNORE_EXCEPTIONS": True,  # mimics memcache behavior.
                                        # http://niwinz.github.io/django-redis/latest/#_memcached_exceptions_behavior
        }
    }
}


########## WSGI SERVER
INSTALLED_APPS += ['gunicorn']


########## EMAIL
DEFAULT_FROM_EMAIL = environ.get('DEFAULT_FROM_EMAIL',
        'Django Packages <djangopackages-noreply@djangopackages.com>')
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = environ.get('EMAIL_HOST', 'smtp.sendgrid.com')
EMAIL_HOST_PASSWORD = os.environ.get('SENDGRID_PASSWORD', '')
EMAIL_HOST_USER = os.environ.get('SENDGRID_USERNAME', '')
EMAIL_PORT = environ.get('EMAIL_PORT', 587)
EMAIL_SUBJECT_PREFIX = environ.get('EMAIL_SUBJECT_PREFIX', '[Django Packages] ')
EMAIL_USE_TLS = True
SERVER_EMAIL = EMAIL_HOST_USER


########## SECRET
SECRET_KEY = environ.get('SECRET_KEY', '')


########## SITE
SITE_TITLE = environ.get('SITE_TITLE')
FRAMEWORK_TITLE = environ.get('FRAMEWORK_TITLE')


########## STORAGE
STATICFILES_STORAGE = 'whitenoise.django.GzipManifestStaticFilesStorage'


########### Permissions
RESTRICT_PACKAGE_EDITORS = False
RESTRICT_GRID_EDITORS = False

########### Errors
# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}


########## DATABASE CONFIGURATION
# ------------------------------------------------------------------------------
# Raises ImproperlyConfigured exception if DATABASE_URL not in os.environ
DATABASES['default'] = env.db("DATABASE_URL")
########## END DATABASE CONFIGURATION

########## django-secure

INSTALLED_APPS += ["djangosecure", ]
MIDDLEWARE_CLASSES = ('djangosecure.middleware.SecurityMiddleware',) + MIDDLEWARE_CLASSES

# set this to 60 seconds and then to 518400 when you can prove it works
SECURE_HSTS_SECONDS = 60
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_FRAME_DENY = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SECURE_SSL_REDIRECT = True

########## end django-secure


########## templates
TEMPLATE_LOADERS = (
    ('django.template.loaders.cached.Loader', (
        'django.template.loaders.filesystem.Loader',
        'django.template.loaders.app_directories.Loader',
    )),
)

########## end templates

########## appenlight-client
import appenlight_client.client as e_client
APPENLIGHT = e_client.get_config({'appenlight.api_key': environ.get('APPENLIGHT_KEY', '')})

MIDDLEWARE_CLASSES = (
    'appenlight_client.django_middleware.AppenlightMiddleware',
) + MIDDLEWARE_CLASSES
########## end appenlight-client
