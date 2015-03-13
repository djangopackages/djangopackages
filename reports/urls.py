from django.conf.urls import patterns, url

from reports.views import package_csv

urlpatterns = patterns("",

    url(
        regex=r"^package/$",
        view=package_csv,
        name="package_csv",
    ),
)