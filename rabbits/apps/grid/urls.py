from django.conf.urls.defaults import *

from grid.models import Grid

from grid.views import grid, grids, add_grid, edit_grid, edit_element

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
        regex = '^(?P<slug>[a-z0-9\-\_]+)/$',
        view    = grid,
        name    = 'grid',
    ), 
    
    url(
        regex = '^element/(?P<feature_id>\d+)/(?P<package_id>\d+)/$',
        view    = edit_element,
        name    = 'edit_element',
    ),       
)
