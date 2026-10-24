"""Which packages a grid compares.

The bar is `settings.PACKAGE_SCORE_MIN`. A grid where nothing clears it
is not shown empty when there is still something worth comparing: for a
grid holding more than one package, anything scoring above zero is
shown instead. A score of exactly zero is left out either way, since
that is where a stale package with a couple of stars lands.
"""

from __future__ import annotations

from django.conf import settings
from django.db.models import Case, Count, F, Q, Value, When

# The fallback bar: strictly above zero.
FALLBACK_SCORE_MIN = 1


def cutoff_for(grid) -> int:
    """The score a package needs to appear in this grid's comparison table."""
    from package.models import Package

    in_grid = Package.objects.active().filter(gridpackage__grid=grid)
    if in_grid.filter(score__gte=settings.PACKAGE_SCORE_MIN).exists():
        return settings.PACKAGE_SCORE_MIN
    if in_grid.count() > 1:
        return FALLBACK_SCORE_MIN
    return settings.PACKAGE_SCORE_MIN


def annotate_active_count(grids):
    """`active_gridpackage_count`: how many packages the grid's table shows.

    The same rule as `cutoff_for`, in SQL, so the grid list agrees with
    the grid pages. Also annotates `gridpackage_count`.
    """
    return grids.annotate(
        # `distinct=True` is required for several Count annotations on the
        # same join not to multiply each other.
        gridpackage_count=Count("gridpackage", distinct=True),
        _above_min=Count(
            "gridpackage",
            filter=Q(gridpackage__package__score__gte=settings.PACKAGE_SCORE_MIN),
            distinct=True,
        ),
        _above_zero=Count(
            "gridpackage",
            filter=Q(gridpackage__package__score__gte=FALLBACK_SCORE_MIN),
            distinct=True,
        ),
    ).annotate(
        active_gridpackage_count=Case(
            When(_above_min__gt=0, then=F("_above_min")),
            When(gridpackage_count__gt=1, then=F("_above_zero")),
            default=Value(0),
        )
    )
