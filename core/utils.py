from django.conf import settings
from django.core.cache import cache
from django.template.defaultfilters import slugify

import re
import requests


def cache_fetcher(cachekey_func, identifier_model):
    key = cachekey_func(identifier_model)
    return (key, cache.get(key))


def oc_slugify(value):
    value = value.replace('.', '-')
    return slugify(value)


def get_pypi_url(title):
    title = title.strip()
    for value in [oc_slugify(title.lower()), oc_slugify(title), title, title.lower(), title.title(), ]:
        value = 'http://pypi.python.org/pypi/' + value
        r = requests.get(value)
        if r.status_code == 200:
            return value
    return None


STATUS_CHOICES = (
    (0, "Unknown"),
    (1, "Development Status :: 1 - Planning"),
    (2, "Development Status :: 2 - Pre-Alpha"),
    (3, "Development Status :: 3 - Alpha"),
    (4, "Development Status :: 4 - Beta"),
    (5, "Development Status :: 5 - Production/Stable"),
    (6, "Development Status :: 6 - Mature"),
    (7, "Development Status :: 7 - Inactive")
)


def status_choices_switch(status):
    for key, value in STATUS_CHOICES:
        if status == value:
            return key


def get_repo_from_url(url):
    """
        Needs to account for:

            1. GitHub Design
            2. Ability to assign special CNAME for BitBucket repos
            3. et al
    """

    # Handle github repos
    if url.startswith("https://github.com/"):
        m = re.match(settings.URL_REGEX_GITHUB, url)
        if m:
            return m.group()

    return None


def healthcheck(url):
    """
    Sends a get request to the given URL
    """
    if settings.HEALTHCHECK:
        for i in range(0, 4):
            r = requests.get(url=url)
            if r.status_code == 200:
                return



