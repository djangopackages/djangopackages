from django.http import HttpResponseNotFound
from django.core.urlresolvers import reverse

from jsonview.decorators import json_view

from grid.models import Grid


@json_view
def grid_detail(request, slug):
    """
    {
        absolute_url: "/grids/g/cms/"
        created: "Sat, 14 Aug 2010 20:12:46 -0400"
        description: "This page lists a few well-known reusable Content Management System applications for Django and tries to gather a comparison of essential features in those applications."
        is_locked: false
        modified: "Sat, 11 Sep 2010 14:57:16 -0400"
        packages: [
            "/api/v1/package/django-cms/"
            "/api/v1/package/django-page-cms/"
            "/api/v1/package/django-lfc/"
            "/api/v1/package/merengue/"
            "/api/v1/package/mezzanine/"
            "/api/v1/package/philo/"
            "/api/v1/package/pylucid/"
            "/api/v1/package/django-gitcms/"
            "/api/v1/package/django-simplepages/"
            "/api/v1/package/djpcms/"
            "/api/v1/package/feincms/"
        ]
        resource_uri: "/api/v1/grid/cms/"
        slug: "cms"
        title: "CMS"
    }
    """
    try:
        grid = Grid.objects.get(slug=slug)
    except Grid.DoesNotExist:
        return HttpResponseNotFound()

    return {
        "absolute_url": grid.get_absolute_url(),
        "created": grid.created,
        "description": grid.description,
        "is_locked": grid.is_locked,
        "modified": grid.modified,
        "resource_uri": request.path,
        "slug": grid.slug,
        "title": grid.title,
        "packages": [
            reverse("apiv3:package_detail", kwargs={'slug':x.slug}) for x in grid.packages.all()
        ]
    }


def grid_list(request):
    pass


@json_view
def package_detail(request, slug):
    return {}
