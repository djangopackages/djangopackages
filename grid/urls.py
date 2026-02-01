"""grid url patterns"""

from django.urls import path
from django.views.decorators.cache import cache_page

from grid.views import (
    AddGridView,
    AjaxGridSearchView,
    EditGridView,
    GridDetailView,
    GridListView,
    AddFeatureView,
    AddGridPackageView,
    AjaxPackageSearchView,
    GridOpenGraphView,
    DeleteFeatureView,
    DeleteGridPackageView,
    EditElementView,
    EditFeatureView,
    GridTimesheetView,
)
from package.views import PackageByGridListView

urlpatterns = [
    path(
        "add/",
        view=AddGridView.as_view(),
        name="add_grid",
    ),
    path(
        "<slug:slug>/edit/",
        view=EditGridView.as_view(),
        name="edit_grid",
    ),
    path(
        "element/<slug:grid_slug>/<int:package_id>/<int:feature_id>/",
        view=EditElementView.as_view(),
        name="edit_element",
    ),
    path(
        "feature/add/<slug:grid_slug>/",
        view=AddFeatureView.as_view(),
        name="add_feature",
    ),
    path(
        "feature/<int:id>/",
        view=EditFeatureView.as_view(),
        name="edit_feature",
    ),
    path(
        "feature/<int:id>/delete/",
        view=DeleteFeatureView.as_view(),
        name="delete_feature",
    ),
    path(
        "package/<slug:grid_slug>/<int:package_id>/delete/",
        view=DeleteGridPackageView.as_view(),
        name="delete_grid_package",
    ),
    path(
        "<slug:grid_slug>/package/add/",
        view=AddGridPackageView.as_view(),
        name="add_grid_package",
    ),
    path(
        "ajax_package_search/",
        view=AjaxPackageSearchView.as_view(),
        name="ajax_package_search",
    ),
    path(
        "ajax_grid_search/",
        view=AjaxGridSearchView.as_view(),
        name="ajax_grid_search",
    ),
    path(
        "",
        view=GridListView.as_view(),
        name="grids",
    ),
    path(
        "g/<slug:slug>/",
        view=GridDetailView.as_view(),
        name="grid",
    ),
    path(
        "g/<slug:slug>/opengraph/",
        view=cache_page(60 * 60 * 24)(GridOpenGraphView.as_view()),
        name="grid_opengraph",
    ),
    path(
        "g/<slug:slug>/timesheet/",
        view=GridTimesheetView.as_view(),
        name="grid_timesheet",
    ),
    path(
        "g/<slug:slug>/packages/",
        view=PackageByGridListView.as_view(),
        name="grid_packages",
    ),
]
