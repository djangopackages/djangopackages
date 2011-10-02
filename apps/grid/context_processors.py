from itertools import izip, chain, repeat

from django.core.urlresolvers import reverse
from django.core.cache import cache

from grid.models import Grid

def grouper(n, iterable, padvalue=None):
    "grouper(3, 'abcdefg', 'x') --> ('a','b','c'), ('d','e','f'), ('g','x','x')"
    return izip(*[chain(iterable, repeat(padvalue, n-1))]*n)

def grid_headers(request):
    cache_key = 'grid_headers'
    grid_headers = cache.get(cache_key)
    if grid_headers is None:
        grid_headers = list(Grid.objects.filter(header=True))
        grid_headers = grouper(7, grid_headers)
        cache.set(cache_key, grid_headers, 60 * 5)
    return {'grid_headers': grid_headers}
