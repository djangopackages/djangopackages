from .base import *

DEBUG = False
TEMPLATE_DEBUG = False
SERVE_MEDIA = False

EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = '587'
EMAIL_HOST_USER = 'djangopackages-noreply@djangopackages.com'
EMAIL_USE_TLS = True

# no try/except here since these not being populated would be bad

# get DATABASES, GONDOR_REDIS_HOST, GONDOR_REDIS_PORT, GONDOR_REDIS_PASSWORD
from local_settings import *

# get EMAIL_HOST_PASSWORD, SECRET_KEY
from .secret import *

