from django.conf.urls.defaults import *

from searchv1.views import (
    search, find_grids_autocomplete, find_packages_autocomplete, search_by_function_autocomplete,
    search_by_category_autocomplete)
    

urlpatterns = patterns("",
    
    url(
        regex   = '^$',
        view    = search,
        name    = 'search',
    ),    
    url(
        regex   = '^grids/autocomplete/$',
        view    = search_by_function_autocomplete,
        name    = 'search_grids_autocomplete',
        kwargs  = dict(
            search_function=find_grids_autocomplete,        
            )        
        
    ),    
    url(
        regex   = '^packages/autocomplete/$',
        view    = search_by_function_autocomplete,
        name    = 'search_packages_autocomplete',
        kwargs  = dict(
            search_function=find_packages_autocomplete,        
            )
    ),
    url(
        regex   = '^packages/by-category/autocomplete/$',
        view    = search_by_category_autocomplete,
        name    = 'search_by_category_autocomplete',
    ),    
)
