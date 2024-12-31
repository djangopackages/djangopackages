from django.conf import settings
from django.core.cache import cache
from django.db.models import Max
from django.urls import reverse

from searchv2.models import SearchV2


def core_values(request):
    """
    A nice pun. But this is how we stick handy data everywhere.

    """
    if cache.get("max_weight"):
        max_weight = cache.get("max_weight")
    else:
        max_weight = SearchV2.objects.only("weight").aggregate(
            max_weight=Max("weight")
        )["max_weight"]
        cache.set("max_weight", max_weight, timeout=60 * 60)

    data = {
        "FRAMEWORK_TITLE": getattr(settings, "FRAMEWORK_TITLE", "Django"),
        "MAX_WEIGHT": max_weight,
        "SITE_TITLE": getattr(settings, "SITE_TITLE", "Django Packages"),
    }
    return data


def current_path(request):
    """Adds the path of the current page to template context, but only
    if it's not the path to the logout page. This allows us to redirect
    user's back to the page they were viewing before they logged in,
    while making sure we never redirect them back to the logout page!

    """
    context = {}
    if request.path.strip() != reverse("logout"):
        context["current_path"] = request.path
    return context


def settings_context(request):
    return {
        "TEST_MODE": settings.TEST_MODE,
    }
