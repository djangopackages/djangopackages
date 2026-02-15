# TODO(searchv3): Remove this urlconf after searchv3 is stable and searchv2 is fully retired.

from django.conf import settings
from django.urls import include, path

urlpatterns = [
    path("search/", include("searchv3.urls")),
    path("", include(settings.ROOT_URLCONF)),
]
