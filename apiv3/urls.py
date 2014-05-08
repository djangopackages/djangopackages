from django.conf.urls import patterns, url

from . import views

urlpatterns = patterns("",
    url(
        regex=r"^grids/$",
        view=views.grid_list,
        name="grid_list",
    ),
    url(
        regex=r"^grids/(?P<slug>[-\w]+)/$",
        view=views.grid_detail,
        name="grid_detail",
    ),
    url(
        regex=r"^packages/$",
        view=views.package_list,
        name="package_list",
    ),
    url(
        regex=r"^packages/(?P<slug>[-\w]+)/$",
        view=views.package_detail,
        name="package_detail",
    ),
    url(
        regex=r"^categories/$",
        view=views.category_list,
        name="category_list"
    ),
    url(
        regex=r"^categories/(?P<slug>[-\w]+)/$",
        view=views.category_detail,
        name="category_detail"
    ),
    url(
        regex=r"^users/(?P<github_account>[-\w]+)/$",
        view=views.user_detail,
        name="user_detail"
    ),
    url(
        regex=r"^users/$",
        view=views.user_list,
        name="user_list"
    )
)
