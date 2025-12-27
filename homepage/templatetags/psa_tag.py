from django import template

from homepage.models import PSA

register = template.Library()


@register.inclusion_tag("new/partials/public_service_announcement.html")
def psa():
    try:
        psa = PSA.objects.latest()
    except PSA.DoesNotExist:
        psa = None
    return {"psa": psa}
