from django.conf.urls.defaults import *

from grid.models import Grid

from grid.views import (
        add_feature,
        add_grid, 
        delete_feature,
        edit_element,
        edit_grid,
        edit_feature,
        grid, 
        grids
    )

urlpatterns = patterns("",
    url(
        regex = '^/$',
        view    = grids,
        name    = 'grids',
    ),
    
    url(
        regex = '^add/$',
        view    = add_grid,
        name    = 'add_grid',
    ),    
    
    url(
        regex = '^(?P<slug>[a-z0-9\-\_]+)/edit/$',
        view    = edit_grid,
        name    = 'edit_grid',
    ),    
    
    url(
        regex = '^g/(?P<slug>[a-z0-9\-\_]+)/$',
        view    = grid,
        name    = 'grid',
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
        regex = '^feature/(?P<id>\d+)/delete$',
        view    = delete_feature,
        name    = 'delete_feature',
    ),       
)
