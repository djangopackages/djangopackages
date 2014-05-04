from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404

from jsonview.decorators import json_view

from grid.models import Grid


@json_view
def grid_detail(request, slug):
    grid = get_object_or_404(Grid, slug=slug)

    return {
        "absolute_url": grid.get_absolute_url(),
        "created": grid.created,
        "description": grid.description,
        "is_locked": grid.is_locked,
        "modified": grid.modified,
        "resource_uri": request.path,
        "slug": grid.slug,
        "title": grid.title,
        "header": grid.header,
        "packages": [
            reverse("apiv3:package_detail", kwargs={'slug':x.slug}) for x in grid.packages.all()
        ]
    }


def grid_list(request):
    pass


@json_view
def package_detail(request, slug):
    return {}
