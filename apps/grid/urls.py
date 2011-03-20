"""grid url patterns"""
from django.conf.urls.defaults import *
from django.views.generic.date_based import archive_index

from grid.models import Grid

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
        grid_detail_feature,
        grids
    )

urlpatterns = patterns("",

    
    url(
        regex = '^add/$',
        view    = add_grid,
        name    = 'add_grid',
    ),    
    
    url(
        regex = '^(?P<slug>[-\w]+)/edit/$',
        view    = edit_grid,
        name    = 'edit_grid',
    ),    
    
    url(
        regex = '^g/(?P<slug>[-\w]+)/$',
        view    = grid_detail,
        name    = 'grid',
# Note: Uncomment the following if you are working on grid rotation, grid permissions, 
#  or other grid detail related code.  This is @sontek's new grid detail template.
#  The grid_detail2.html file will replace grid_detail.html once it is fully stable
#  in all browsers and production-ready.
#        kwargs  = {'template_name': 'grid/grid_detail2.html'},
    ), 
    
    url(
        regex = '^element/(?P<feature_id>\d+)/(?P<package_id>\d+)/$',
        view    = edit_element,
        name    = 'edit_element',
    ),  
    
    url(
        regex = '^feature/add/(?P<grid_slug>[a-z0-9\-\_]+)/$',
        view    = add_feature,
        name    = 'add_feature',
    ),         
    
    url(
        regex = '^feature/(?P<id>\d+)/$',
        view    = edit_feature,
        name    = 'edit_feature',
    ), 
    
    url(
        regex = '^feature/(?P<id>\d+)/delete/$',
        view    = delete_feature,
        name    = 'delete_feature',
    ),       

    url(
        regex = '^package/(?P<id>\d+)/delete/$',
        view    = delete_grid_package,
        name    = 'delete_grid_package',
    ),       

    url(
        regex = '^(?P<grid_slug>[a-z0-9\-\_]+)/package/add/$',
        view    = add_grid_package,
        name    = 'add_grid_package',
    ),           

    url(
        regex = '^(?P<grid_slug>[a-z0-9\-\_]+)/package/add/new$',
        view    = add_new_grid_package,
        name    = 'add_new_grid_package',
    ),

    url(
        regex = '^ajax_grid_list/$',
        view    = ajax_grid_list,
        name    = 'ajax_grid_list',
    ),    

    url(
        regex   = r"^latest/$",
        view    = archive_index,
        name    = "latest_grids",
        kwargs  = dict(
            queryset=Grid.objects.select_related(),     
            date_field='created'   
            )            
    ),

    url(
        regex = '^$',
        view    = grids,
        name    = 'grids',
    ),    
    
    url(
        regex = '^g/(?P<slug>[-\w]+)/(?P<feature_id>\d+)/(?P<bogus_slug>[-\w]+)/$',
        view    = grid_detail_feature,
        name    = 'grid_detail_feature',
    ),
    
)
