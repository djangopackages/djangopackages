from django.conf import settings
from django.core.urlresolvers import reverse
from django.db.models import Max
from django.utils.html import escape

from searchv2.models import SearchV2

def core_values(request):
    """
    A nice pun. But this is how we stick handy data everywhere.
    """

    data = {
        'SITE_TITLE': getattr(settings, "SITE_TITLE", "Django Packages"),
        'FRAMEWORK_TITLE': getattr(settings, "FRAMEWORK_TITLE", "Django"),
        'MAX_WEIGHT': SearchV2.objects.all().aggregate(Max('weight'))['weight__max']
        }
    return data


def current_path(request):
    """Adds the path of the current page to template context, but only
    if it's not the path to the logout page. This allows us to redirect
    user's back to the page they were viewing before they logged in,
    while making sure we never redirect them back to the logout page!

    """
    context = {}
    if request.path.strip() != reverse('logout'):
        context['current_path'] = request.path

        # fix for https://github.com/djangopackages/djangopackages/issues/517
        context['current_path'] = escape(context['current_path'])
        context['current_path'] = context['current_path'].replace("{{", "&#123;&#123;").replace("}}", "&#124;&#124;")

    return context
