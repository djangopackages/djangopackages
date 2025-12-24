from django import template
from django.db.models import Count
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from grid.models import Grid
from package.models import Package

register = template.Library()


@register.inclusion_tag("new/partials/grid_of_the_week.html")
def grid_of_the_week():
    today = timezone.now().date()

    potw = (
        Package.objects.active()
        .annotate(grid_count=Count("gridpackage"))
        .filter(dpotw__start_date__lte=today, dpotw__end_date__gte=today)
        .order_by("-dpotw__start_date", "-dpotw__end_date")
        .first()
    )
    gotw = (
        Grid.objects.all()
        .annotate(package_count=Count("gridpackage"), feature_count=Count("feature"))
        .filter(gotw__start_date__lte=today, gotw__end_date__gte=today)
        .order_by("-gotw__start_date", "-gotw__end_date")
        .first()
    )
    return {
        "potw": potw,
        "gotw": gotw,
    }
