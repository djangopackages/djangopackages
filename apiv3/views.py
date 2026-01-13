from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404
from jsonview.decorators import json_view

from grid.models import Grid
from package.models import Category, Package
from profiles.models import Profile

from .resources import category_resource, grid_resource, package_resource, user_resource


def get_optimized_package_queryset():
    """Return a Package queryset optimized to avoid N+1 queries in package_resource()."""
    return Package.objects.select_related(
        "created_by__profile",
        "last_modified_by__profile",
        "category",
    ).prefetch_related(
        Prefetch("gridpackage_set__grid"),
    )


def get_optimized_grid_queryset():
    """Return a Grid queryset optimized to avoid N+1 queries in grid_resource()."""
    return Grid.objects.prefetch_related("packages")


def GET_int(request, value_name, default):
    try:
        value = int(request.GET.get(value_name, default))
    except ValueError:
        value = default
    return value


def calc_next(request, limit, offset, count):
    # calculate next
    if count > limit + offset:
        next = f"{request.path}?limit={limit}&offset={offset + limit}"
    else:
        next = None
    return next


def calc_previous(request, limit, offset, count):
    # calculate previous
    if offset <= 0:
        previous = None
    else:
        previous = "{}?limit={}&offset={}".format(
            request.path, limit, max(offset - limit, 0)
        )
    return previous


@json_view
def grid_detail(request, slug):
    grid = get_object_or_404(get_optimized_grid_queryset(), slug=slug)
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
            "total_count": count,
        },
        "objects": [
            grid_resource(x)
            for x in get_optimized_grid_queryset()[offset : offset + limit]
        ],
    }


@json_view
def package_detail(request, slug):
    package = get_object_or_404(get_optimized_package_queryset(), slug=slug)
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
            "total_count": count,
        },
        "category": None,
    }

    qs = get_optimized_package_queryset()
    if category:
        qs = qs.filter(category=category)

    data["objects"] = [package_resource(x) for x in qs[offset : offset + limit]]

    return data


@json_view
def category_list(request):
    count = Category.objects.count()
    limit = GET_int(request, "limit", 20)
    offset = GET_int(request, "offset", 0)

    # Return the Data structure
    return {
        "meta": {
            "limit": limit,
            "next": calc_next(request, limit, offset, count),
            "offset": offset,
            "previous": calc_previous(request, limit, offset, count),
            "total_count": count,
        },
        "objects": [
            category_resource(x)
            for x in Category.objects.all()[offset : offset + limit]
        ],
    }


@json_view
def category_detail(request, slug):
    category = get_object_or_404(Category, slug=slug)
    return category_resource(category)


@json_view
@login_required
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
            "total_count": count,
        },
        "objects": [
            user_resource(x, list_packages)
            for x in Profile.objects.select_related("user")[offset : offset + limit]
        ],
    }


@json_view
@login_required
def user_detail(request, github_account):
    profile = get_object_or_404(
        Profile.objects.select_related("user"), github_account=github_account
    )
    list_packages = request.GET.get("list_packages", False)
    return user_resource(profile, list_packages)


@json_view
def grid_packages_list(request, slug):
    grid = get_object_or_404(get_optimized_grid_queryset(), slug=slug)
    packages = get_optimized_package_queryset().filter(grid=grid)
    count = packages.count()
    limit = GET_int(request, "limit", 20)
    offset = GET_int(request, "offset", 0)
    # build the Data structure
    data = {
        "meta": {
            "limit": limit,
            "next": calc_next(request, limit, offset, count),
            "offset": offset,
            "previous": calc_previous(request, limit, offset, count),
            "total_count": count,
        },
        "grid": grid_resource(grid),
        "objects": [package_resource(x) for x in packages[offset : offset + limit]],
    }
    return data


@json_view
def index(request):
    return {
        "categories": "/api/v3/categories/",
        "grids": "/api/v3/grids/",
        "packages": "/api/v3/packages/",
        "users": "/api/v3/users/",
    }
