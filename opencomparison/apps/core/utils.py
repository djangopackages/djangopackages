from django.core.cache import cache

def cache_fetcher(cachekey_func, identifier_model):
    key = cachekey_func(identifier_model)
    return (key, cache.get(key))
