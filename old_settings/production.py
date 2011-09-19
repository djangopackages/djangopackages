from .base import *

DEBUG = False
TEMPLATE_DEBUG = False
SERVE_MEDIA = False

# local_settings.py can be used to override environment-specific settings
# like database and email that differ between development and production.
try:
    from local_settings import *
except ImportError:
    pass