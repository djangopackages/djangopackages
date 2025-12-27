from django.urls import path

from profiles import views

urlpatterns = [
    path("edit/", view=views.ProfileEditUpdateView.as_view(), name="profile_edit"),
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
