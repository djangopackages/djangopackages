from django.conf.urls.defaults import *
from django.views.generic.list_detail import object_detail, object_list
from django.views.generic.simple import direct_to_template

from package.models import Package
from package.views import add_package, edit_package

urlpatterns = patterns("",
    url(
        regex   = r"^$",
        view    = object_list,
        name    = "package_index",
        kwargs  = dict(
            queryset=Package.objects.select_related(),        
            )
            
    ),
    
    url(
        regex   = '^add/$',
        view    = add_package,
        name    = 'add_package',
    ),    

    url(
        regex = '^(?P<slug>[a-z0-9\-\_]+)/edit$',
        view    = edit_package,
        name    = 'edit_package', 
    ),    

    
    url(
        regex = '^(?P<slug>[a-z0-9\-\_]+)/$',
        view    = object_detail,
        name    = 'package',
        kwargs=dict(
            queryset=Package.objects.select_related(),
            template_name='package/package.html',
            )    
    ),    
    
)
