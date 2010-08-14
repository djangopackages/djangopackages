from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User 
from django.core.urlresolvers import reverse 
from django.http import HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import render_to_response, get_object_or_404 
from django.template import RequestContext 

from grid.models import Grid

def grids(request, template_name="grid/grids.html"):
    
    return render_to_response(template_name, {
        'grids': Grid.objects.all(),
        },
        context_instance=RequestContext(request)
        )

def grid(request, slug, template_name="grid/grid.html"):
    
    grid = get_object_or_404(Grid, slug=slug)

    return render_to_response(template_name, {
        'grid': grid,
        },
        context_instance=RequestContext(request)
        )
