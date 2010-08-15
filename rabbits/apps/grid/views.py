from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User 
from django.core.urlresolvers import reverse 
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404 
from django.template import RequestContext 


from grid.forms import ElementForm, FeatureForm, GridForm, GridPackageForm
from grid.models import Element, Feature, Grid, GridPackage
from package.models import Package

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
        
@login_required
def add_feature(request, grid_slug, template_name="grid/add_feature.html"):

    grid = get_object_or_404(Grid, slug=grid_slug)
    feature = Feature()
    form = FeatureForm(request.POST or None, instance=feature)    

    if form.is_valid(): 
        feature = Feature(
                    grid=grid, 
                    title=request.POST['title'],
                    description = request.POST['description']
                )
        feature.save()
        return HttpResponseRedirect(reverse('grid', kwargs={'slug':feature.grid.slug}))


    return render_to_response(template_name, { 
        'form': form,
        'grid':grid
        },
        context_instance=RequestContext(request))           
        
@login_required
def edit_feature(request, id, template_name="grid/edit_feature.html"):

    feature = get_object_or_404(Feature, id=id)
    form = FeatureForm(request.POST or None, instance=feature)

    if form.is_valid():
        feature = form.save()
        return HttpResponseRedirect(reverse('grid', kwargs={'slug': feature.grid.slug}))

    return render_to_response(template_name, { 
        'form': form,  
        }, 
        context_instance=RequestContext(request))
        
@login_required
def delete_feature(request, id, template_name="grid/edit_feature.html"):

    feature = get_object_or_404(Feature, id=id)
    Element.objects.filter(feature=feature).delete()
    feature.delete()

    return HttpResponseRedirect(reverse('grid', kwargs={'slug': feature.grid.slug}))


@login_required
def delete_grid_package(request, id, template_name="grid/edit_feature.html"):

    package = get_object_or_404(GridPackage, id=id)
    Element.objects.filter(grid_package=package).delete()
    package.delete()

    return HttpResponseRedirect(reverse('grid', kwargs={'slug': package.grid.slug}))

        
@login_required
def edit_element(request, feature_id, package_id, template_name="grid/edit_element.html"):
    
    feature = get_object_or_404(Feature, id=feature_id)
    grid_package = get_object_or_404(GridPackage, id=package_id)    
    element = get_object_or_404(Element, feature=feature, grid_package=grid_package)
    
    form = ElementForm(request.POST or None, instance=element)

    if form.is_valid():
        element = form.save()
        return HttpResponseRedirect(reverse('grid', kwargs={'slug': feature.grid.slug}))

    return render_to_response(template_name, { 
        'form': form,  
        }, 
        context_instance=RequestContext(request))        

@login_required
def add_grid_package(request, grid_slug, template_name="grid/add_grid_package.html"):

    grid = get_object_or_404(Grid, slug=grid_slug)
    grid_package = GridPackage()
    form = GridPackageForm(request.POST or None, instance=grid_package)    

    if form.is_valid(): 
        package = get_object_or_404(Package, id=request.POST['package'])
        package = GridPackage(
                    grid=grid, 
                    package=package
                )
        package.save()
        return HttpResponseRedirect(reverse('grid', kwargs={'slug':grid.slug}))


    return render_to_response(template_name, { 
        'form': form,
        'grid': grid
        },
        context_instance=RequestContext(request))
        
