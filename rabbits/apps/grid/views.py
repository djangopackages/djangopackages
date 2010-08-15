from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User 
from django.core.urlresolvers import reverse 
from django.http import HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import render_to_response, get_object_or_404 
from django.template import RequestContext 
from django.views.decorators.csrf import csrf_protect

from grid.forms import GridForm
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
        
@login_required
@csrf_protect
def add_grid(request, template_name="grid/add_grid.html"):

    new_grid = Grid()
    form = GridForm(request.POST or None, instance=new_grid)    

    if form.is_valid(): 
        new_grid = form.save()
        return HttpResponseRedirect(reverse('grid', kwargs={'slug':new_grid.slug}))


    return render_to_response(template_name, { 
        'form': form
        },
        context_instance=RequestContext(request))
        
@login_required
@csrf_protect
def edit_grid(request, slug, template_name="grid/edit_grid.html"):

    grid = get_object_or_404(Grid, slug=slug)
    form = GridForm(request.POST or None, instance=grid)

    if form.is_valid():
        grid = form.save()
        return HttpResponseRedirect(reverse('grid', kwargs={'slug': grid.slug}))

    return render_to_response(template_name, { 
        'form': form,  
        }, 
        context_instance=RequestContext(request))        