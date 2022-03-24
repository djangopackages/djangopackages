from django.db.models import Count
from itertools import chain, repeat

from grid.models import Grid


def grouper(n, iterable, padvalue=None):
    "grouper(3, 'abcdefg', 'x') --> ('a','b','c'), ('d','e','f'), ('g','x','x')"
    return zip(*[chain(iterable, repeat(padvalue, n - 1))] * n)


def grid_headers(request):
    grid_headers = list(
        Grid.objects.filter(header=True)
        .annotate(gridpackage_count=Count("gridpackage"))
        .filter(gridpackage_count__gt=2)
        .order_by("title")
    )
    grid_headers = grouper(7, grid_headers)
    return {"grid_headers": grid_headers}
