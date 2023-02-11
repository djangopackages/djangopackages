"""grid url patterns"""

from django.urls import path, re_path

from grid import views
from grid.views import (
    GridListView,
    add_feature,
    add_grid,
    add_grid_package,
    add_new_grid_package,
    ajax_grid_list,
    delete_feature,
    delete_grid_package,
    edit_element,
    edit_feature,
    edit_grid,
    grid_detail,
    grid_opengraph_detail,
)

urlpatterns = [
    path(
        "add/",
        view=add_grid,
        name="add_grid",
    ),
    path(
        "<slug:slug>/edit/",
        view=edit_grid,
        name="edit_grid",
    ),
    path(
        "element/<int:feature_id>/<int:package_id>/",
        view=edit_element,
        name="edit_element",
    ),
    re_path(
        r"^feature/add/(?P<grid_slug>[a-z0-9\-\_]+)/$",
        view=add_feature,
        name="add_feature",
    ),
    path(
        "feature/<int:id>/",
        view=edit_feature,
        name="edit_feature",
    ),
    path(
        "feature/<int:id>/delete/",
        view=delete_feature,
        name="delete_feature",
    ),
    path(
        "package/<int:id>/delete/",
        view=delete_grid_package,
        name="delete_grid_package",
    ),
    re_path(
        r"^(?P<grid_slug>[a-z0-9\-\_]+)/package/add/$",
        view=add_grid_package,
        name="add_grid_package",
    ),
    re_path(
        r"^(?P<grid_slug>[a-z0-9\-\_]+)/package/add/new$",
        view=add_new_grid_package,
        name="add_new_grid_package",
    ),
    path(
        "ajax_grid_list/",
        view=ajax_grid_list,
        name="ajax_grid_list",
    ),
    path(
        "",
        view=GridListView.as_view(),
        name="grids",
    ),
    path(
        "g/<slug:slug>/",
        view=grid_detail,
        name="grid",
    ),
    path(
        "g/<slug:slug>/opengraph/",
        view=grid_opengraph_detail,
        name="grid_opengraph",
    ),
    path(
        "g/<slug:slug>/landscape/",
        view=views.grid_detail_landscape,
        name="grid_landscape",
    ),
    path("g/<slug:slug>/timesheet/", view=views.grid_timesheet, name="grid_timesheet"),
]
