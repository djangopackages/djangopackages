from django.core.cache import cache
from django.template.defaultfilters import slugify

def cache_fetcher(cachekey_func, identifier_model):
    key = cachekey_func(identifier_model)
    return (key, cache.get(key))

def oc_slugify(value):
    value = value.replace('.', '-')
    return slugify(value)
