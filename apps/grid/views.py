"""views for the :mod:`apps.grid` app"""
from django.db.models import Count
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import User 
from django.core.urlresolvers import reverse 
from django.http import HttpResponseRedirect, Http404 
from django.shortcuts import render_to_response, get_object_or_404 
from django.template import RequestContext 


from grid.forms import ElementForm, FeatureForm, GridForm, GridPackageForm
from grid.models import Element, Feature, Grid, GridPackage
from package.models import Package
from package.forms import PackageForm
from package.views import repo_data_for_js

def build_element_map(elements):
    # Horrifying two-level dict due to needing to use hash() function later
    element_map = {}
    for element in elements:
        element_map.setdefault(element.feature_id, {})
        element_map[element.feature_id][element.grid_package_id] = element
    return element_map

def grids(request, template_name="grid/grids.html"):
    """lists grids

    Template context:

    * ``grids`` - all grid objects
    """
    # annotations providing bad counts
    #grids = Grid.objects.annotate(gridpackage_count=Count('gridpackage'), feature_count=Count('feature'))
    return render_to_response(
        template_name, {
            'grids': Grid.objects.all(),
        }, context_instance = RequestContext(request)
    )

def grid_detail(request, slug, template_name="grid/grid_detail.html"):
    """displays a grid in detail

    Template context:

    * ``grid`` - the grid object
    * ``elements`` - elements of the grid
    * ``features`` - feature set used in the grid
    * ``grid_packages`` - packages involved in the current grid
    """
    grid = get_object_or_404(Grid, slug=slug)
    features = grid.feature_set.all()

    gp = grid.gridpackage_set.select_related('gridpackage', 'package__repo', 'package__category')
    grid_packages = gp.annotate(usage_count=Count('package__usage')).order_by('-usage_count', 'package')

    elements = Element.objects.all() \
                .filter(feature__in=features,
                        grid_package__in=grid_packages)

    element_map = build_element_map(elements)

    default_attributes = [('repo_description', 'Description'), 
                ('Category',), ('pypi_downloads', 'Downloads'), ('last_updated', 'Last Updated'), ('pypi_version', 'Version'),
                ('repo', 'Repo'), ('commits_over_52', 'Commits'), ('repo_watchers', 'Repo watchers'), ('repo_forks', 'Forks'),
                ('participant_list', 'Participants')
            ]

    return render_to_response(
        template_name, {
            'grid': grid,
            'features': features,
            'grid_packages': grid_packages,
            'attributes': default_attributes,
            'elements': element_map,
        }, context_instance = RequestContext(request)
    )

def grid_detail_feature(request, slug, feature_id, bogus_slug, template_name="grid/grid_detail_feature.html"):
    """a slightly more focused view than :func:`grid.views.grid_detail`
    shows comparison for only one feature, and does not show the basic
    grid parameters

    Template context is the same as in :func:`grid.views.grid_detail`
    """
    grid = get_object_or_404(Grid, slug=slug)
    features = grid.feature_set.filter(id=feature_id)
    if not features.count():
        raise Http404
    grid_packages = grid.gridpackage_set.select_related('gridpackage')

    elements = Element.objects.all() \
                .filter(feature__in=features,
                        grid_package__in=grid_packages)

    element_map = build_element_map(elements)

    return render_to_response(
        template_name, {
            'grid': grid,
            'feature': features[0],
            'grid_packages': grid_packages,
            'elements': element_map,
        }, context_instance = RequestContext(request)
    )

@login_required
def add_grid(request, template_name="grid/add_grid.html"):
    """Creates a new grid, requires user to be logged in.
    Works for both GET and POST request methods

    Template context:

    * ``form`` - an instance of :class:`~app.grid.forms.GridForm`
    """

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
    """View to modify the grid, handles GET and POST requests.
    This view requires user to be logged in.

    Template context:

    * ``form`` - instance of :class:`grid.forms.GridForm`
    """

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
    """Adds a feature to the grid, accepts GET and POST requests.

    Requires user to be logged in

    Template context:

    * ``form`` - instance of :class:`grid.forms.FeatureForm` form
    * ``grid`` - instance of :class:`grid.models.Grid` model
    """

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
    """edits feature on a grid - this view has the same
    semantics as :func:`grid.views.add_feature`.

    Requires the user to be logged in.
    """

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
        
@permission_required('grid.delete_feature')
def delete_feature(request, id, template_name="grid/edit_feature.html"):
    """deletes a feature from the grid, ``id`` is id of the 
    :class:`grid.models.Feature` model that is to be deleted

    Requires permission `grid.delete_feature`.

    Redirects to the parent :func:`grid.views.grid_detail`
    """

    feature = get_object_or_404(Feature, id=id)
    Element.objects.filter(feature=feature).delete()
    feature.delete()

    return HttpResponseRedirect(reverse('grid', kwargs={'slug': feature.grid.slug}))


@permission_required('grid.delete_gridpackage')
def delete_grid_package(request, id, template_name="grid/edit_feature.html"):
    """Deletes package from the grid, ``id`` is the id of the 
    :class:`grid.models.GridPackage` instance

    Requires permission ``grid.delete_gridpackage``.

    Redirects to :func:`grid.views.grid_detail`.
    """


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
    """Add an existing package to this grid."""

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
            grid_package = GridPackage(
                        grid=grid, 
                        package=package
                    )
            grid_package.save()
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

@login_required
def add_new_grid_package(request, grid_slug, template_name="package/package_form.html"):
    """Add a package to a grid that isn't yet represented on the site."""
    
    grid = get_object_or_404(Grid, slug=grid_slug)
    
    new_package = Package()
    form = PackageForm(request.POST or None, instance=new_package)
    
    if form.is_valid():
        new_package = form.save()
        GridPackage.objects.create(
            grid=grid, 
            package=new_package
        )
        return HttpResponseRedirect(reverse("grid", kwargs={"slug":grid_slug}))
    
    return render_to_response(template_name, {
        "form": form,
        "repo_data": repo_data_for_js(),
        "action": "add",
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
