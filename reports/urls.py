from django.conf.urls import url

from reports.views import package_csv

urlpatterns = [

    url(
        regex=r"^package/$",
        view=package_csv,
        name="package_csv",
    ),
]
