from django.urls import path

from searchv2 import views

urlpatterns = [
    path(
        "build/",
        view=views.build_search,
        name="build_search",
    ),
    path(
        "",
        view=views.search2,
        name="search",
    ),
    path(
        "v3/",
        view=views.search3,
        name="search_v3",
    ),
    path(
        "packages/autocomplete/",
        view=views.search_packages_autocomplete,
        name="search_packages_autocomplete",
    ),
    path(
        "opensearch/description/",
        views.OpenSearchDescription.as_view(
            content_type="application/opensearchdescription+xml"
        ),
        name="opensearch-description",
    ),
    path(
        "opensearch/suggestions/",
        views.OpenSearchSuggestions.as_view(),
        name="opensearch-suggestions",
    ),
]
