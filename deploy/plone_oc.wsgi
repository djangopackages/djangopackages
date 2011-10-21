# plone_oc.wsgi is configured to live in <repo_root>/deploy.

import os
import sys
import site

from os.path import abspath, dirname, join
from site import addsitedir

# Virtualenv plone_oc is in ~/.virtualenvs
site_packages = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.virtualenvs/plone_oc/lib/python2.7/site-packages')
site.addsitedir(os.path.abspath(site_packages))

sys.path.insert(0, abspath(join(dirname(__file__), "../../")))

from django.conf import settings
os.environ["DJANGO_SETTINGS_MODULE"] = "plone_oc.settings"
os.environ["CELERY_LOADER"] = "django"

sys.path.insert(0, join(settings.PROJECT_ROOT, "apps"))

from django.core.handlers.wsgi import WSGIHandler
application = WSGIHandler()
