from django.conf.urls.defaults import patterns, url

from package import views as package_views
from grid import views as grid_views

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
)