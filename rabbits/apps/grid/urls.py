from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template
from django.views.generic.list_detail import object_detail

from grid.models import Grid

from grid.views import grid, grids

urlpatterns = patterns("",
    url(
        regex = '^/$',
        view    = grids,
        name    = 'grids',
    ),
    
    url(
        regex = '^(?P<slug>[a-z0-9\-\_]+)/$',
        view    = grid,
        name    = 'grid',
    ),    
)
