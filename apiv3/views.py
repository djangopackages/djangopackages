from django.shortcuts import get_object_or_404

from jsonview.decorators import json_view

from .resources import (
        grid_resource, package_resource, category_resource, user_resource
    )
from grid.models import Grid
from package.models import Package, Category
from profiles.models import Profile


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
            offset + limit
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
            max(offset - limit, 0)
        )
    return previous


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
        "objects": [grid_resource(x) for x in Grid.objects.all()[offset:offset + limit]]
    }


@json_view
def package_detail(request, slug):
    package = get_object_or_404(Package, slug=slug)
    return package_resource(package)


@json_view
def package_list(request):
    category = request.GET.get("category", None)
    try:
        category = Category.objects.get(slug=category)
        count = Package.objects.filter(category=category).count()
    except Category.DoesNotExist:
        category = None
        count = Package.objects.count()

    limit = GET_int(request, "limit", 20)
    offset = GET_int(request, "offset", 0)

    # build the Data structure
    data = {
        "meta": {
            "limit": limit,
            "next": calc_next(request, limit, offset, count),
            "offset": offset,
            "previous": calc_previous(request, limit, offset, count),
            "total_count": count
        },
        "category": None
    }

    if category:
        data['objects'] = [
            package_resource(x) for x in Package.objects.filter(category=category)[offset:offset + limit]
        ]
    else:
        data['objects'] = [package_resource(x) for x in Package.objects.all()[offset:offset + limit]]

    return data


@json_view
def category_list(request):
    count = Profile.objects.count()
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
        "objects": [category_resource(x) for x in Category.objects.all()[offset:offset + limit]]
    }


@json_view
def category_detail(request, slug):
    category = get_object_or_404(Category, slug=slug)
    return category_resource(category)


@json_view
def user_list(request):
    count = Profile.objects.count()
    limit = GET_int(request, "limit", 20)
    offset = GET_int(request, "offset", 0)
    list_packages = request.GET.get("list_packages", False)

    # Return the Data structure
    return {
        "meta": {
            "limit": limit,
            "next": calc_next(request, limit, offset, count),
            "offset": offset,
            "previous": calc_previous(request, limit, offset, count),
            "total_count": count
        },
        "objects": [user_resource(x, list_packages) for x in Profile.objects.all()[offset:offset + limit]]
    }


@json_view
def user_detail(request, github_account):
    profile = get_object_or_404(Profile, github_account=github_account)
    list_packages = request.GET.get("list_packages", False)
    return user_resource(profile, list_packages)
