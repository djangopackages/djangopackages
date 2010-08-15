from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404 
from django.template import RequestContext 

from package.models import Category, Package
from homepage.models import Dpotw, Gotw, Tab

def homepage(request, template_name="homepage.html"):
    
    categories = []
    for category in Category.objects.all():
        packages = category.package_set.all()[:10]
        element = {
            'title':category.title,
            'description':category.description,
            'count': category.package_set.count(),
            'slug':category.slug,
            'packages':category.package_set.order_by('-pypi_downloads', '-repo_watchers', 'title')[:10]
        }
        categories.append(element)
    
    return render_to_response(template_name, {
        'categories': categories,
        'dpotw': Dpotw.objects.get_current(),
        'gotw': Gotw.objects.get_current(),
        'tab': Tab.objects.all()
        },
        context_instance=RequestContext(request)
        )
        