from settings.base import *

import os, sys, urlparse, traceback

DEBUG = False
TEMPLATE_DEBUG = DEBUG
SERVE_MEDIA = DEBUG

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

ROOT_URLCONF = "django_oc.urls"

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