from django.urls import path

from . import views

app_name = "apiv3"

# New URLs
urlpatterns = [
    path(
        "grids/",
        view=views.grid_list,
        name="grid_list",
    ),
    path(
        "grids/<slug:slug>/",
        view=views.grid_detail,
        name="grid_detail",
    ),
    path(
        "grids/<slug:slug>/packages/",
        view=views.grid_packages_list,
        name="grid_packages_list",
    ),
    path(
        "packages/",
        view=views.package_list,
        name="package_list",
    ),
    path(
        "packages/<slug:slug>/",
        view=views.package_detail,
        name="package_detail",
    ),
    path("categories/", view=views.category_list, name="category_list"),
    path("categories/<slug:slug>/", view=views.category_detail, name="category_detail"),
    path("users/<slug:github_account>/", view=views.user_detail, name="user_detail"),
    path("users/", view=views.user_list, name="user_list"),
    path("", view=views.index, name="index"),
]
