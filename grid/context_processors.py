from itertools import chain, repeat

from django.core.cache import cache
from django.db.models import Count

from grid.models import Grid


def grouper(n, iterable, padvalue=None):
    "grouper(3, 'abcdefg', 'x') --> ('a','b','c'), ('d','e','f'), ('g','x','x')"
    return zip(*[chain(iterable, repeat(padvalue, n - 1))] * n)


def grid_headers(request):
    if cache.get("grid_headers"):
        grid_headers = cache.get("grid_headers")
    else:
        grid_headers = list(
            Grid.objects.filter(header=True)
            .only("pk", "slug", "description", "title")
            .annotate(gridpackage_count=Count("gridpackage"))
            .filter(gridpackage_count__gt=2)
            .order_by("title")
        )
        # cache dict for 5 minutes...
        cache.set("grid_headers", grid_headers, timeout=60 * 5)

    grid_headers = grouper(7, grid_headers)
    return {"grid_headers": grid_headers}
