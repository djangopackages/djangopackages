from django.conf.urls import patterns

from package import apiv2 as package_api
from grid import views as grid_views
from searchv2 import views as search_views
from django.urls import path

urlpatterns = patterns(
    "",
    # {% url "apiv2:category" %}
    path(
        "categories/", view=package_api.CategoryListAPIView.as_view(), name="categories"
    ),
    # {% url "apiv2:packages" %}
    path("packages/", view=package_api.PackageListAPIView.as_view(), name="packages"),
    # {% url "apiv2:packages" slug %}
    path(
        "packages/<slug:slug>/",
        view=package_api.PackageDetailAPIView.as_view(),
        name="packages",
    ),
    # {% url "apiv2:grids" %}
    path("grids/", view=grid_views.GridListAPIView.as_view(), name="grids"),
    # {% url "apiv2:grids" slug %}
    path(
        "grids/<slug:slug>/", view=grid_views.GridDetailAPIView.as_view(), name="grids"
    ),
    # {% url "apiv2:search" %}
    path("search/", view=search_views.SearchListAPIView.as_view(), name="search"),
    # {% url "apiv2:search" slug %}
    path(
        "search/<slug:slug>/",
        view=search_views.SearchDetailAPIView.as_view(),
        name="search",
    ),
    # {% url "apiv2:python3" slug %}
    path("python3/", view=package_api.Python3ListAPIView.as_view(), name="python3"),
)
