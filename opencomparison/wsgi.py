import os, sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__)))
sys.path.insert(0, os.path.abspath(os.path.join(PROJECT_ROOT, os.path.pardir))) 

from django.core.handlers.wsgi import WSGIHandler
os.environ["DJANGO_SETTINGS_MODULE"] = "opencomparison.settings.production"
application = WSGIHandler()