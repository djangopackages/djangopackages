from reports.views import package_csv
from django.urls import path

urlpatterns = [
    path(
        "package/",
        view=package_csv,
        name="package_csv",
    ),
]
