"""
heroku addons:add heroku-shared-postgresql
heroku run python manage.py syncdb --settings=settings.prod
heroku run python manage.py migrate --settings=settings.prod
"""

from settings.base import *

import os, sys, urlparse, traceback

DEBUG = False
TEMPLATE_DEBUG = DEBUG
SERVE_MEDIA = True

INSTALLED_APPS += ['gunicorn']
CACHE_TIMEOUT = 60 * 60 * 24

urlparse.uses_netloc.append('postgres')
urlparse.uses_netloc.append('mysql')
try:
    if os.environ.has_key('DATABASE_URL'):
        url = urlparse.urlparse(os.environ['DATABASE_URL'])
        DATABASES = {}
        DATABASES['default'] = {
            'NAME':     url.path[1:],
            'USER':     url.username,
            'PASSWORD': url.password,
            'HOST':     url.hostname,
            'PORT':     url.port,
        }
        if url.scheme == 'postgres':
            DATABASES['default']['ENGINE'] = 'django.db.backends.postgresql_psycopg2'
        if url.scheme == 'mysql':
            DATABASES['default']['ENGINE'] = 'django.db.backends.mysql'
except Exception as e:

    print "Unexpected error:", sys.exc_info()


LOCAL_INSTALLED_APPS = []

LAUNCHPAD_ACTIVE = False

# Analytics ID
URCHIN_ID = ""

# Email Settings
DEFAULT_FROM_EMAIL = \
        'Django Packages <djangopackages-noreply@djangopackages.com>'
EMAIL_SUBJECT_PREFIX = '[Django Packages] '

# See http://celeryproject.org/docs/configuration.html#task-execution-settings
BROKER_BACKEND = "django"

RESTRICT_PACKAGE_EDITORS = False
RESTRICT_GRID_EDITORS = False

ROOT_URLCONF = "app.urls"

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

SECRET_KEY = os.environ.has_key('SECRET_KEY')

GITHUB_API_SECRET = os.environ.has_key('GITHUB_API_SECRET')
GITHUB_APP_ID     = os.environ.has_key('GITHUB_APP_ID')

SITE_TITLE = "Django Packages"
FRAMEWORK_TITLE = "Django"

PIWIK_CODE ="""
<!-- Piwik --> 
<script type="text/javascript">
var pkBaseURL = (("https:" == document.location.protocol) ? "https://manage.cartwheelweb.com/piwik/" : "http://manage.cartwheelweb.com/piwik/");
document.write(unescape("%3Cscript src='" + pkBaseURL + "piwik.js' type='text/javascript'%3E%3C/script%3E"));
</script><script type="text/javascript">
try {
var piwikTracker = Piwik.getTracker(pkBaseURL + "piwik.php", 4);
piwikTracker.trackPageView();
piwikTracker.enableLinkTracking();
} catch( err ) {}
</script><noscript><p><img src="http://manage.cartwheelweb.com/piwik/piwik.php?idsite=4" style="border:0" alt="" /></p></noscript>
<!-- End Piwik Tracking Code -->
"""

########## STORAGE CONFIGURATION

INSTALLED_APPS += ['storages',]

DEFAULT_FILE_STORAGE = 'storages.backends.s3boto.S3BotoStorage'
STATICFILES_STORAGE = 'storages.backends.s3boto.S3BotoStorage'

AWS_QUERYSTRING_AUTH = False

AWS_HEADERS = {
    'Expires': 'Thu, 15 Apr 2020 20:00:00 GMT',
    'Cache-Control': 'max-age=86400',
}

# Boto requires subdomain formatting.
from S3 import CallingFormat
AWS_CALLING_FORMAT = CallingFormat.SUBDOMAIN

# Amazon S3 configuration.
if os.environ.has_key('S3_KEY'):
    AWS_ACCESS_KEY_ID = os.environ['S3_KEY']
    AWS_SECRET_ACCESS_KEY = os.environ['S3_SECRET']
else:
    AWS_ACCESS_KEY_ID = AWS_KEY
    AWS_SECRET_ACCESS_KEY = AWS_SECRET_KEY
    
AWS_STORAGE_BUCKET_NAME = 'opencomparison'

STATIC_URL = 'https://s3.amazonaws.com/opencomparison/'
MEDIA_URL = STATIC_URL
########## END STORAGE CONFIGURATION
