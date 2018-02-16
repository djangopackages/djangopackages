from django.conf.urls import url

from profiles import views

urlpatterns = [
    url(
        regex=r"^edit/$",
        view=views.ProfileEditUpdateView.as_view(),
        name="profile_edit"
    ),
    url(r"^(?P<github_account>[-\w]+)/$", views.profile_detail, name="profile_detail"),
]
