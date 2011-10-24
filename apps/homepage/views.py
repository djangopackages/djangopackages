from random import randrange

from django.db.models import Count
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404 
from django.template import RequestContext

import feedparser

from grid.models import Grid
from homepage.models import Dpotw, Gotw, PSA
from package.models import Category, Package

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

    # get up to 5 random packages
    package_count = Package.objects.count()
    random_packages = []
    if package_count > 1:
        package_ids = set([])
   
        for i in range(10):
            package_ids.add(randrange(1,package_count+1))
        
        for i, package_id in enumerate(package_ids):
            try:
                random_packages.append(Package.objects.get(id=package_id))
            except Package.DoesNotExist:
                pass
            if len(random_packages) == 5:
                break
                
    try:
        potw = Dpotw.objects.latest().package
    except Dpotw.DoesNotExist:
        potw = None
    except Package.DoesNotExist:
        potw = None
        
    try:
        gotw = Gotw.objects.latest().grid
    except Gotw.DoesNotExist:
        gotw = None
    except Grid.DoesNotExist:
        gotw = None        

    # Public Service Announcement on homepage
    try:
        psa_body = PSA.objects.latest().body_text
    except PSA.DoesNotExist:
        psa_body = '<p>There are currently no announcements.  To request a PSA, tweet at <a href="http://twitter.com/open_comparison">@Open_Comparison</a>.</p>'

    # Latest OpenComparison blog post on homepage
    feed = 'http://opencomparison.blogspot.com/feeds/posts/default'
    blogpost_title = feedparser.parse(feed).entries[0].title
    blogpost_body = feedparser.parse(feed).entries[0].summary

    return render_to_response(
        template_name, {
            "latest_packages":Package.objects.all().order_by('-created')[:5],
            "random_packages": random_packages,
            "potw": potw,
            "gotw": gotw,
            "psa_body": psa_body,
            "blogpost_title": blogpost_title,
            "blogpost_body": blogpost_body,
            "categories":categories,
            "package_count":package_count
        }, context_instance = RequestContext(request)
    )
        