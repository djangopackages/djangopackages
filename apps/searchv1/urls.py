from django.conf.urls.defaults import *

from searchv1.views import search

urlpatterns = patterns("",
    
    url(
        regex   = '^$',
        view    = search,
        name    = 'search',
    ),    
)
