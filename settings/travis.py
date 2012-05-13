# -*- coding: utf-8 -*-
"""TravisCI settings which allow us to run our test suite on the TravisCI
continuous integration service.
"""


from settings.test import *


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
        "USER": "",
        "PASSWORD": "",
        "HOST": "",
        "PORT": "",
    },
}
