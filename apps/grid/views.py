from django.db.models import Count
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User 
from django.core.urlresolvers import reverse 
from django.http import HttpResponseRedirect, Http404 
from django.shortcuts import render_to_response, get_object_or_404 
from django.template import RequestContext 


from grid.forms import ElementForm, FeatureForm, GridForm, GridPackageForm
from grid.models import Element, Feature, Grid, GridPackage
from package.models import Package

def grids(request, template_name="grid/grids.html"):
    grids = Grid.objects.all().annotate(gridpackage_count=Count('gridpackage'), feature_count=Count('feature'))
    return render_to_response(
        template_name, {
            'grids': grids,
        }, context_instance = RequestContext(request)
    )

def grid_detail(request, slug, template_name="grid/grid_detail.html"):
    grid = get_object_or_404(Grid, slug=slug)
    features = grid.feature_set.all()
    
    gp = grid.gridpackage_set.select_related('gridpackage', 'package__repo', 'package__category')
    grid_packages = gp.annotate(usage_count=Count('package__usage')).order_by('-usage_count', 'package')
    
    # Get a list of all elements for this grid, and then package them into a
    # dictionary so we can easily lookup the element for every
    # feature/grid_package combination.
    elements_mapping = {}
    all_elements = Element.objects.all().filter(feature__in=features, grid_package__in=grid_packages)
    for element in all_elements:
        grid_mapping = elements_mapping.setdefault(element.feature_id, {})
        grid_mapping[element.grid_package_id] = element
    
    return render_to_response(
        template_name, {
            'grid': grid,
            'features': features,
            'grid_packages': grid_packages,
            'elements': elements_mapping,
        }, context_instance = RequestContext(request)
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
        'grid': grid
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
        'grid': feature.grid  
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
    
    feature = get_object_or_404(Feature, pk=feature_id)
    grid_package = get_object_or_404(GridPackage, pk=package_id)    
    
    # Sanity check to make sure both the feature and grid_package are related to
    # the same grid!
    if feature.grid_id != grid_package.grid_id:
        raise Http404
    
    element, created = Element.objects.get_or_create(
                                    grid_package=grid_package,
                                    feature=feature
                                    )    
        
    form = ElementForm(request.POST or None, instance=element)

    if form.is_valid():
        element = form.save()
        return HttpResponseRedirect(reverse('grid', kwargs={'slug': feature.grid.slug}))

    return render_to_response(template_name, { 
        'form': form,
        'feature':feature,
        'package':grid_package.package,
        'grid':feature.grid
        }, 
        context_instance=RequestContext(request))        

@login_required
def add_grid_package(request, grid_slug, template_name="grid/add_grid_package.html"):

    grid = get_object_or_404(Grid, slug=grid_slug)
    grid_package = GridPackage()
    form = GridPackageForm(request.POST or None, instance=grid_package)    
    message = ''

    if form.is_valid(): 
        package = get_object_or_404(Package, id=request.POST['package'])    
        try:
            GridPackage.objects.get(grid=grid, package=package)
            message = "Sorry, but '%s' is already in this grid." % package.title
        except GridPackage.DoesNotExist:
            package = GridPackage(
                        grid=grid, 
                        package=package
                    )
            package.save()
            redirect = request.POST.get('redirect','')
            if redirect:
                return HttpResponseRedirect(redirect)
            
            return HttpResponseRedirect(reverse('grid', kwargs={'slug':grid.slug}))
    


    return render_to_response(template_name, { 
        'form': form,
        'grid': grid,
        'message': message
        },
        context_instance=RequestContext(request))
        

def ajax_grid_list(request, template_name="grid/ajax_grid_list.html"):
    q = request.GET.get('q','')
    grids = []
    if q:
        grids = Grid.objects.filter(title__istartswith=q)
    package_id = request.GET.get('package_id','')
    if package_id:
        grids = grids.exclude(gridpackage__package__id=package_id)
    return render_to_response(template_name, {
        'grids': grids
        },
        context_instance=RequestContext(request)
    )