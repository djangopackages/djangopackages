from django.conf import settings
from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template
from django.views.generic.list_detail import object_list

from django.contrib import admin
admin.autodiscover()

from homepage.views import homepage
from package.views import package_autocomplete, category


urlpatterns = patterns("",

    url('', include('social_auth.urls')),
    url(r"^$", homepage, name="home"),
    url(r"^admin/", include(admin.site.urls)),
    url(r"^profiles/", include("profiles.urls")),
    url(r"^packages/", include("package.urls")),
    url(r"^grids/", include("grid.urls")),
    url(r"^feeds/", include("feeds.urls")),

    url(r"^categories/(?P<slug>[-\w]+)/$", category, name="category"),
    url(r"^categories/$", homepage, name="categories"),

    url(r'^login/$', direct_to_template, {'template': 'pages/login.html', }, 'login',),
    url(r'^logout/$', 'django.contrib.auth.views.logout_then_login', {}, 'logout',),

    # static pages
    url(r"^about/$", direct_to_template, {"template": "pages/about.html"}, name="about"),
    url(r"^terms/$", direct_to_template, {"template": "pages/terms.html"}, name="terms"),
    url(r"^faq/$", direct_to_template, {"template": "pages/faq.html"}, name="faq"),    
    url(r"^syndication/$", direct_to_template, {"template": "pages/syndication.html"}, name="syndication"),
    url(r"^contribute/$", direct_to_template, {"template": "pages/contribute.html"}, name="contribute"),
    url(r"^search/", include("searchv2.urls")),
    url(r"^importer/", include("importer.urls")),
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
        url(r"", include("django.contrib.staticfiles.urls")),
    )
