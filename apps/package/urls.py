from django.conf.urls.defaults import *
from django.views.generic.dates import ArchiveIndexView

from package.models import Package
from package.views import (
                            add_example, 
                            add_package, 
                            ajax_package_list,                             
                            edit_package, 
                            edit_example, 
                            update_package,
                            usage,
                            package_list,
                            package_detail
                            )

urlpatterns = patterns("",

    url(
        regex   = r"^$",
        view    = package_list,
        name    = "packages",
    ),
    
    url(
        regex   = r"^latest/$",
        view    = ArchiveIndexView.as_view(
                        queryset=Package.objects.select_related(), 
                        date_field="created"   
        ),
        name    = "latest_packages",          
    ),
    
    
    url(
        regex   = "^add/$",
        view    = add_package,
        name    = "add_package",
    ),    

    url(
        regex = "^(?P<slug>[-\w]+)/edit/$",
        view    = edit_package,
        name    = "edit_package", 
    ),    
    
    url(
        regex = "^(?P<slug>[-\w]+)/fetch-data/$",
        view    = update_package,
        name    = "fetch_package_data", 
    ),    

    url(
        regex = "^(?P<slug>[-\w]+)/example/add/$",
        view    = add_example,
        name    = "add_example", 
    ),    
    
    url(
        regex = "^(?P<slug>[-\w]+)/example/(?P<id>\d+)/edit/$",
        view    = edit_example,
        name    = "edit_example", 
    ),    
    
    url(
        regex = "^p/(?P<slug>[-\w]+)/$",
        view    = package_detail,
        name    = "package",
    ),      
        
    url(
        regex = "^ajax_package_list/$",
        view    = ajax_package_list,
        name    = "ajax_package_list",
    ), 
    
    url(
        regex = "^usage/(?P<slug>[-\w]+)/(?P<action>add|remove)/$",
        view    = usage,
        name    = "usage",
    ),
   
        
)
