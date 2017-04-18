from django.conf.urls import url

from searchv2 import views

urlpatterns = [

    url(
        regex='^build$',
        view=views.build_search,
        name='build_search',
    ),

    url(
        regex='^$',
        view=views.search2,
        name='search',
    ),

    url(
        regex='^packages/autocomplete/$',
        view=views.search_packages_autocomplete,
        name='search_packages_autocomplete',
    ),

]
