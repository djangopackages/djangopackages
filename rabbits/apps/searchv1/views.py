from django.db.models import Q
from django.shortcuts import render_to_response
from django.template import RequestContext 

from grid.models import Grid
from package.models import Package

from searchv1.forms import SearchForm


def search(request, template_name='searchv1/search.html'):
    """
    Searches in Grids and Packages
    """
    grids = []
    packages = []
    q = request.GET.get('q', '')
    if q:
        packages = Package.objects.filter(Q(title__icontains=q) | Q(repo_description__icontains=q))
        grids    = Grid.objects.filter(Q(title__icontains=q) | Q(description__icontains=q))
        
    form = SearchForm(request.GET or None)
        
    return render_to_response(template_name, {
        'grids': grids,
        'packages': packages,
        'form':form
        },
        context_instance=RequestContext(request)
    )