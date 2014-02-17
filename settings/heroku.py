# -*- coding: utf-8 -*-
"""Heroku specific settings. These are used to deploy opencomparison to
Heroku's platform.
"""


from os import environ

from memcacheify import memcacheify
from postgresify import postgresify
from S3 import CallingFormat

from settings.base import *


########## CACHE
CACHE_TIMEOUT = 60 * 60 * 24 * 30
CACHES = memcacheify()


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


########## GITHUB
GITHUB_API_SECRET = environ.get('GITHUB_API_SECRET')
GITHUB_APP_ID = environ.get('GITHUB_APP_ID')


########## SITE
SITE_TITLE = environ.get('SITE_TITLE')
FRAMEWORK_TITLE = environ.get('FRAMEWORK_TITLE')


########## STORAGE
INSTALLED_APPS += ['storages']
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto.S3BotoStorage'
STATICFILES_STORAGE = 'storages.backends.s3boto.S3BotoStorage'

AWS_ACCESS_KEY_ID = environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = environ.get('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = environ.get('AWS_STORAGE_BUCKET_NAME')

AWS_CALLING_FORMAT = CallingFormat.SUBDOMAIN
AWS_HEADERS = {
    'Expires': 'Thu, 15 Apr 2020 20:00:00 GMT',
    'Cache-Control': 'max-age=86400',
}
AWS_QUERYSTRING_AUTH = False

STATIC_URL = 'https://s3.amazonaws.com/%s/' % AWS_STORAGE_BUCKET_NAME
MEDIA_URL = STATIC_URL


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
# Setting PGSQL_POOLING to True means:
#   We use django_postgrespool to handle the database connection.
#   What this means is we use SqlAlchemy to handle the pool to PGSQL on Heroku, meaning we don't have
#   to reestablish connection to the database as often. Which means a faster app. The downside is there
#   is some risk as it's still a new project.
#
# Setting PGSQL_POOLING to False means:
#   We use the standard Django pgsql connection. The pooling isn't as good but we have more stability.
PGSQL_POOLING = False


if PGSQL_POOLING:
    import dj_database_url

    DATABASES = {'default': dj_database_url.config()}
    DATABASES['default']['ENGINE'] = 'django_postgrespool'

    SOUTH_DATABASE_ADAPTERS = {
        'default': 'south.db.postgresql_psycopg2'
    }

    DATABASE_POOL_ARGS = {
        'max_overflow': 10,
        'pool_size': 5,
        'recycle': 300
    }
else:
    from postgresify import postgresify

    DATABASES = postgresify()
########## END DATABASE CONFIGURATION


########## sslify
MIDDLEWARE_CLASSES = ('sslify.middleware.SSLifyMiddleware',) + MIDDLEWARE_CLASSES
########## end sslify

########## django-secure

INSTALLED_APPS += ["djangosecure", ]

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