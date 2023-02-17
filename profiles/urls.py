from django.urls import path

from profiles import views

urlpatterns = [
    path("edit/", view=views.ProfileEditUpdateView.as_view(), name="profile_edit"),
    path("<slug:github_account>/", views.profile_detail, name="profile_detail"),
]
