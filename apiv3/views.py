from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404

from jsonview.decorators import json_view

from grid.models import Grid
from package.models import Package


def base_resource(obj):
    return {
        "absolute_url": obj.get_absolute_url(),
        "created": obj.created,
        "modified": obj.modified,
        "slug": obj.slug,
        "title": obj.title,
    }

def grid_resource(grid):
    data = base_resource(grid)
    data.update(
        {
            "description": grid.description,
            "is_locked": grid.is_locked,
            "resource_uri": reverse("apiv3:grid_detail", kwargs={"slug": grid.slug}),
            "header": grid.header,
            "packages": [
                reverse("apiv3:package_detail", kwargs={'slug':x.slug}) for x in grid.packages.all()
            ]
        }
    )
    return data
    
def package_resource(package):
    data = base_resource(package)
    
    if package.created_by is None:
        created_by = None
    else:
        created_by = reverse("user_detail", kwargs={"github_account": package.created_by.github_account})
    
    data.update(
        {
            "category": reverse("apiv3:category_detail", kwargs={"slug": package.category.slug}),
            "commit_list": package.commit_list,
            "commits_over_52": package.commit_list,
            "created_by": created_by,
            "documentation_url": package.documentation_url,
            "grids": [],  #TODO
            "last_fetched": package.last_fetched
        }
    )
    return data
    
def GET_int(request, value_name, default):
    try:
        value = int(request.GET.get(value_name, default))
    except ValueError:
        value = default
    return value
    
def calc_next(request, limit, offset, count):
    # calculate next
    if count > limit + offset:
        next = "{}?limit={}&offset={}".format(
            request.path,
            limit,
            offset+limit
        )
    else:
        next = None
    return next
    
def calc_previous(request, limit, offset, count):
    
    # calculate previous
    if offset <= 0:
        previous = None
    else:
        previous = "{}?limit={}&offset={}".format(
            request.path,
            limit,
            max(offset-limit, 0)
        )    

@json_view
def grid_detail(request, slug):
    grid = get_object_or_404(Grid, slug=slug)
    return grid_resource(grid)



@json_view
def grid_list(request):
    count = Grid.objects.count()
    limit = GET_int(request, "limit", 20)
    offset = GET_int(request, "offset", 0)
    
        
    # Return the Data structure
    return {
        "meta": {
            "limit": limit,
            "next": calc_next(request, limit, offset, count),
            "offset": offset,
            "previous": calc_previous(request, limit, offset, count),
            "total_count": count
        },
        "objects": [grid_resource(x) for x in Grid.objects.all()[offset:offset+limit]]
    }


@json_view
def package_detail(request, slug):
    package = get_object_or_404(Package, slug=slug)
    return package_resource(package)

@json_view
def category_detail(request, slug):
    return {}
    
@json_view
def user_detail(request, github_account):
    return {}