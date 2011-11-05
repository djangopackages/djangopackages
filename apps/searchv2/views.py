import simplejson

from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.http import HttpResponseForbidden, HttpResponseRedirect, HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext

from package.models import Package
from searchv2.forms import SearchForm
from searchv2.builders import build_1
from searchv2.models import SearchV2
from searchv2.utils import remove_prefix, clean_title

@login_required
def build_search(request, template_name="searchv2/build_results.html"):
    
    if not request.user.is_superuser:
        return HttpResponseForbidden()
        
    results = []
    if request.method == 'POST':
        results = build_1(False)

    return render_to_response(template_name,
                {'results':results},
                context_instance=RequestContext(request))
    
def search_function(q):
    """ TODO - make generic title searches have lower weight """
    
    items = []
    if q:
        items = SearchV2.objects.filter(
                    Q(clean_title__startswith=clean_title(remove_prefix(q))) |
                    Q(title__icontains=q) | 
                    Q(title_no_prefix__startswith=q.lower()) |
                    Q(slug__startswith=q.lower()) | 
                    Q(slug_no_prefix__startswith=q.lower()))
        #grids    = Grid.objects.filter(Q(title__icontains=q) | Q(description__icontains=q))
    return items
    
def search(request, template_name='searchv2/search.html'):
    """
    Searches in Grids and Packages
    """
    q = request.GET.get('q', '')
    
    if '/' in q:
        lst = q.split('/')
        try:
            if lst[-1]:
                q = lst[-1]
            else:
                q = lst[-2]
        except IndexError:
            pass
    try:
        package = Package.objects.get(title=q)
        url = reverse("package", args=[package.slug.lower()])
        return HttpResponseRedirect(url)
    except Package.DoesNotExist:
        pass
        
    try:
        package = Package.objects.get(slug=q)
        url = reverse("package", args=[package.slug.lower()])
        return HttpResponseRedirect(url)
    except Package.DoesNotExist:
        pass

    form = SearchForm(request.GET or None)

    return render_to_response(template_name, {
        'items': search_function(q),
        'form':form
        },
        context_instance=RequestContext(request)
    )
    
def search_packages_autocomplete(request):
    """
    Searches in Packages
    """
    q = request.GET.get('term', '')
    form = SearchForm(request.GET or None)  
    if q:
        objects    = search_function(q)[:15]
        objects    = objects.values_list('title', flat=True)    
        json_response = simplejson.dumps(list(objects))
    else:
        json_response = simplejson.dumps([])

    return HttpResponse(json_response, mimetype='text/javascript')
    