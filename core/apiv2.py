from django.conf.urls.defaults import patterns, url

from package import views as package_views
from grid import views as grid_views
from searchv2 import views as search_views

urlpatterns = patterns("",
    # {% url "apiv2:packages" %}
    url(
        regex=r"packages/$",
        view=package_views.PackageListAPIView.as_view(),
        name="packages"
    ),
    # {% url "apiv2:packages" slug %}
    url(
        regex=r"packages/(?P<slug>[-\w]+)/$",
        view=package_views.PackageDetailAPIView.as_view(),
        name="packages"
    ),
    # {% url "apiv2:grids" %}
    url(
        regex=r"grids/$",
        view=grid_views.GridListAPIView.as_view(),
        name="grids"
    ),
    # {% url "apiv2:grids" slug %}
    url(
        regex=r"grids/(?P<slug>[-\w]+)/$",
        view=grid_views.GridDetailAPIView.as_view(),
        name="grids"
    ),
    # {% url "apiv2:search" %}
    url(
        regex=r"search/$",
        view=search_views.SearchListAPIView.as_view(),
        name="search"
    ),
    # {% url "apiv2:search" slug %}
    url(
        regex=r"search/(?P<slug>[-\w]+)/$",
        view=search_views.SearchDetailAPIView.as_view(),
        name="search"
    ),
    # {% url "apiv2:python3" slug %}
    url(
        regex=r"python3/$",
        view=package_views.Python3ListAPIView.as_view(),
        name="python3"
    ),
)