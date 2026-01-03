from django.urls import path

from profiles import views

urlpatterns = [
    path("edit/", view=views.ProfileUpdateView.as_view(), name="profile_edit"),
    path(
        "extra-field/add/",
        views.ProfileExtraFieldCreateView.as_view(),
        name="profile_add_extra_field",
    ),
    path(
        "extra-field/<int:pk>/edit/",
        views.ProfileExtraFieldUpdateView.as_view(),
        name="profile_edit_extra_field",
    ),
    path(
        "extra-field/<int:pk>/delete/",
        views.ProfileDeleteExtraFieldView.as_view(),
        name="profile_delete_extra_field",
    ),
    path(
        "<slug:github_account>/",
        views.ProfileDetailView.as_view(),
        name="profile_detail",
    ),
    path(
        "<slug:github_account>/contributed/",
        views.ProfileContributedPackagesView.as_view(),
        name="profile_contributed_packages",
    ),
    path(
        "<slug:github_account>/favorites/",
        views.ProfileFavoritePackagesView.as_view(),
        name="profile_favorite_packages",
    ),
]
