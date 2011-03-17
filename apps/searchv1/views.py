import simplejson

from django.conf import settings
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext 

from grid.models import Grid
from package.models import Package

from searchv1.forms import SearchForm

def package_search(q):
    django_dash = '%s-%s' % (settings.PACKAGINATOR_SEARCH_PREFIX, q)
    django_space = '%s %s' % (settings.PACKAGINATOR_SEARCH_PREFIX, q)
    return Package.objects.filter(
                Q(title__istartswith=q) | 
                Q(title__istartswith=django_dash) |
                Q(title__istartswith=django_space) |
                Q(slug__istartswith=q) | 
                Q(slug__istartswith=django_dash) |
                Q(slug__istartswith=django_space)                
                )    

def find_packages_autocomplete(q):
    return package_search(q)[:15]

def find_grids_autocomplete(q):
    return Grid.objects.filter(title__istartswith=q)[:15]

def search_by_function_autocomplete(request, search_function):
    """
    Searches in Grids and Packages
    """
    q = request.GET.get('term', '')
    form = SearchForm(request.GET or None)  
    if q:
        objects    = search_function(q)
        objects    = objects.values_list('title', flat=True)    
        json_response = simplejson.dumps(list(objects))
    else:
        json_response = simplejson.dumps([])

    return HttpResponse(json_response, mimetype='text/javascript')
    
def search_by_category_autocomplete(request):
    """
    Search by categories on packages
    """    
    q = request.GET.get('term', '')
    packages = package_search(q)    
    ex_cat = request.GET.get('ex_cat', '')
    print ex_cat
    if ex_cat.strip():
        for cat in ex_cat.split(','):            
            packages = packages.exclude(category__slug=cat)
    
    package = packages[:15]
    
    objects = packages.values_list('title', flat=True) 
    json_response = simplejson.dumps(list(objects))
    return HttpResponse(json_response, mimetype='text/javascript')    
    

def search(request, template_name='searchv1/search.html'):
    """
    Searches in Grids and Packages
    """
    grids = []
    packages = []
    q = request.GET.get('q', '')
    try:
        package = Package.objects.get(title=q)
        url = reverse("package", args=[package.slug.lower()])
        return HttpResponseRedirect(url)
        
    except Package.DoesNotExist:
        pass
    if q:
        django_dash = '%s-%s' % (settings.PACKAGINATOR_SEARCH_PREFIX, q)
        django_space = '%s %s' % (settings.PACKAGINATOR_SEARCH_PREFIX, q)
        packages = Package.objects.filter(
                    Q(title__icontains=q) | 
                    Q(title__istartswith=django_dash) |
                    Q(title__istartswith=django_space) | 
                    Q(slug__istartswith=q) | 
                    Q(slug__istartswith=django_dash) |
                    Q(slug__istartswith=django_space) |                                       
                    Q(repo_description__icontains=q))        
        grids    = Grid.objects.filter(Q(title__icontains=q) | Q(description__icontains=q))
        
    form = SearchForm(request.GET or None)
        
    return render_to_response(template_name, {
        'grids': grids,
        'packages': packages,
        'form':form
        },
        context_instance=RequestContext(request)
    )