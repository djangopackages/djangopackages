from homepage.models import Tab

def grid_tabs(request):
    context = {}
    # TODO: Cache theses...
    context['grid_tabs'] = Tab.objects.all().select_related('grid')
    return context