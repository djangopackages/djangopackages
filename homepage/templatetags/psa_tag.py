from django import template
from django.db.models import Count
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from grid.models import Grid
from homepage.models import PSA
from package.models import Package

register = template.Library()


@register.inclusion_tag("new/partials/public_service_announcement.html")
def psa():
    try:
        psa = PSA.objects.latest()
    except PSA.DoesNotExist:
        psa = None
    return {"psa": psa}
