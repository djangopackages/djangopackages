from django.core.urlresolvers import reverse
from django.core.cache import cache

from homepage.models import Tab

def grid_tabs(request):
    grid_tabs = cache.get('sitewide:grid_tabs')
    if grid_tabs is None:
        grid_tabs = Tab.objects.all().select_related('grid')
        cache.set('sitewide:grid_tabs', grid_tabs, 300)
    return {'grid_tabs': grid_tabs}

def current_path(request):
    """Adds the path of the current page to template context, but only
    if it's not the path to the logout page. This allows us to redirect
    user's back to the page they were viewing before they logged in,
    while making sure we never redirect them back to the logout page!
    
    """
    context = {}
    if request.path != reverse('acct_logout'):
        context['current_path'] = request.path
    return context