# this is a hack to work around https://code.djangoproject.com/ticket/15064
# normally we'd just set DJANGO_SETTINGS_MODULE to opencomparison.settings.development and call it a day
# this way if you run ./manage.py without specifying a --settings you'll get the dev settings
from .development import *