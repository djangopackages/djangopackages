from django.conf.urls import patterns, url

from . import views

urlpatterns = patterns("",
    url(
        regex=r"^grid/(?P<slug>[-\w]+)/$",
        view=views.grid_detail,
        name="grid_detail",
    ),
    url(
        regex=r"^package/(?P<slug>[-\w]+)/$",
        view=views.package_detail,
        name="package_detail",
    ),
)
