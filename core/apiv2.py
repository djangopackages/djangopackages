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
)