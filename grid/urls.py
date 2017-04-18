"""grid url patterns"""
from django.conf.urls import url

from grid import views

from grid.views import (
        add_feature,
        add_grid,
        add_grid_package,
        add_new_grid_package,
        ajax_grid_list,
        delete_feature,
        delete_grid_package,
        edit_element,
        edit_grid,
        edit_feature,
        grid_detail,
        grids
    )

urlpatterns = [

    url(
        regex='^add/$',
        view=add_grid,
        name='add_grid',
    ),

    url(
        regex='^(?P<slug>[-\w]+)/edit/$',
        view=edit_grid,
        name='edit_grid',
    ),

    url(
        regex='^element/(?P<feature_id>\d+)/(?P<package_id>\d+)/$',
        view=edit_element,
        name='edit_element',
    ),

    url(
        regex='^feature/add/(?P<grid_slug>[a-z0-9\-\_]+)/$',
        view=add_feature,
        name='add_feature',
    ),

    url(
        regex='^feature/(?P<id>\d+)/$',
        view=edit_feature,
        name='edit_feature',
    ),

    url(
        regex='^feature/(?P<id>\d+)/delete/$',
        view=delete_feature,
        name='delete_feature',
    ),

    url(
        regex='^package/(?P<id>\d+)/delete/$',
        view=delete_grid_package,
        name='delete_grid_package',
    ),

    url(
        regex='^(?P<grid_slug>[a-z0-9\-\_]+)/package/add/$',
        view=add_grid_package,
        name='add_grid_package',
    ),

    url(
        regex='^(?P<grid_slug>[a-z0-9\-\_]+)/package/add/new$',
        view=add_new_grid_package,
        name='add_new_grid_package',
    ),

    url(
        regex='^ajax_grid_list/$',
        view=ajax_grid_list,
        name='ajax_grid_list',
    ),


    url(
        regex='^$',
        view=grids,
        name='grids',
    ),

    url(
        regex='^g/(?P<slug>[-\w]+)/$',
        view=grid_detail,
        name='grid',
    ),

    url(
        regex='^g/(?P<slug>[-\w]+)/landscape/$',
        view=views.grid_detail_landscape,
        name='grid_landscape',
    ),
    url(regex='^g/(?P<slug>[-\w]+)/timesheet/$',
        view=views.grid_timesheet,
        name='grid_timesheet'
    )
]
