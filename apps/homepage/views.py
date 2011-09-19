from random import shuffle

from django.db.models import Count
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404 
from django.template import RequestContext 

from package.models import Category, Package
from homepage.models import Dpotw, Gotw

def homepage(request, template_name="homepage.html"):
    
    categories = []
    for category in Category.objects.annotate(package_count=Count("package")):
        element = {
            "title":category.title,
            "description":category.description,
            "count": category.package_count,
            "slug": category.slug,
            "title_plural": category.title_plural,
            "show_pypi": category.show_pypi,
        }
        categories.append(element)

    # get random packages
    packages = Package.objects.all()
    package_count = packages.count()
    count_list = [x for x in range(package_count)]
    shuffle(count_list)
    random_packages = [packages[x] for x in count_list[:5]]
    
    return render_to_response(
        template_name, {
            "latest_packages":Package.objects.all().order_by('-created')[:5],
            "random_packages": random_packages,
            "dpotw": Dpotw.objects.get_current(),
            "gotw": Gotw.objects.get_current(),
            "categories":categories,
            "package_count":package_count
        }, context_instance = RequestContext(request)
    )
        