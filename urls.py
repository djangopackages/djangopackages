from django.conf import settings
from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template
from django.views.generic.list_detail import object_list

from django.contrib import admin
admin.autodiscover()

from homepage.views import homepage
from package.views import package_autocomplete, category, packaginate


urlpatterns = patterns("",

    url(r"^$", homepage, name="home"),
    url(r"^admin/", include(admin.site.urls)),
    url(r"^about/", include("about.urls")),
    url(r"^profiles/", include("profiles.urls")),
    url(r"^notices/", include("notification.urls")),
    url(r"^packages/", include("package.urls")),
    url(r"^grids/", include("grid.urls")),  
    url(r"^search/", include("searchv1.urls")),
    url(r"^feeds/", include("feeds.urls")),
    
    url(r"^categories/(?P<slug>[-\w]+)/$", category, name="category"),
    url(r"^categories/$", homepage, name="categories"),
    url(r"^packaginator/$", 
                direct_to_template,
                {'template': 'package/packaginator.html'}, 
                name="packaginator"), 
                
    url(r"^packaginate/$", 
                packaginate,
                name="packaginate"),                   
    
    url(
        regex = '^autocomplete/package/$',
        view = package_autocomplete,
        name    = 'package_autocomplete',        
    ),

    #TODO - fix these by using django-registration
    url(r"^account/login/$", direct_to_template, {"template": "about/about.html"}, name="acct_login"),    
    url(r"^signup/$", direct_to_template, {"template": "about/about.html"}, name="acct_signup"), 
    url(r"^logout/$", direct_to_template, {"template": "about/about.html"}, name="acct_logout"), 
    url(r"^email/$", direct_to_template, {"template": "about/about.html"}, name="acct_email"), 
    
)

from apiv1.api import Api
from apiv1.resources import (
                    GotwResource, DpotwResource,
                    PackageResource, CategoryResource,
                    GridResource, PackageResourceBase,
                    UserResource
                    )

v1_api = Api()
v1_api.register(PackageResourceBase())
v1_api.register(PackageResource())
v1_api.register(CategoryResource())
v1_api.register(GridResource())
v1_api.register(GotwResource())
v1_api.register(DpotwResource())
v1_api.register(UserResource())

urlpatterns += patterns('',
    url(r"^api/", include(v1_api.urls)), 
)


if settings.SERVE_MEDIA:
    urlpatterns += patterns("",
        url(r"", include("staticfiles.urls")),
    )
