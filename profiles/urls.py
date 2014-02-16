from django.conf.urls.defaults import patterns, url

from profiles import views

urlpatterns = patterns("",
    url(
        regex=r"^edit/$",
        view=views.ProfileEditUpdateView.as_view(),
        name="profile_edit"
    ),
    url(r"^$", views.profile_list, name="profile_list"),
    url(r"^(?P<github_account>[-\w]+)/$", views.profile_detail, name="profile_detail"),
)
