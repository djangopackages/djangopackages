from django.core.cache import cache
from django.template.defaultfilters import slugify

import requests

def cache_fetcher(cachekey_func, identifier_model):
    key = cachekey_func(identifier_model)
    return (key, cache.get(key))

def oc_slugify(value):
    value = value.replace('.', '-')
    return slugify(value)

def get_pypi_url(title):
    title = title.strip()
    for value in [title, title.lower(), oc_slugify(title), title.title()]:
        value = 'http://pypi.python.org/pypi/' + value
        r = requests.get(value)
        if r.status_code == 200:
            return value
    return None