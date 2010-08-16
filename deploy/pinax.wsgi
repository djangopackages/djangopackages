# pinax.wsgi is configured to live in projects/rabbits/deploy.

import os
import sys
import site

from os.path import abspath, dirname, join
from site import addsitedir

site_packages = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'env/lib/python2.6/site-packages')
site.addsitedir(os.path.abspath(site_packages))

sys.path.insert(0, abspath(join(dirname(__file__), "../../")))

from django.conf import settings
os.environ["DJANGO_SETTINGS_MODULE"] = "djangopackages.settings"

sys.path.insert(0, join(settings.PROJECT_ROOT, "apps"))

from django.core.handlers.wsgi import WSGIHandler
application = WSGIHandler()

