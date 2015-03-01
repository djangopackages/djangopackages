from django.conf import settings
from django.conf.urls import patterns, url, include
from django.conf.urls.static import static
from django.views.generic.base import TemplateView, RedirectView


from django.contrib import admin
admin.autodiscover()

from homepage.views import homepage, error_404_view, error_500_view, py3_compat
from package.views import category

urlpatterns = patterns("",

    url(r'^login/\{\{item\.absolute_url\}\}/', RedirectView.as_view(url="/login/github/")),
    url('', include('social_auth.urls')),
    url(r"^$", homepage, name="home"),
    url(r"^404$", error_404_view, name="404"),
    url(r"^500$", error_500_view, name="500"),
    url(settings.ADMIN_URL_BASE, include(admin.site.urls)),
    url(r"^profiles/", include("profiles.urls")),
    url(r"^packages/", include("package.urls")),
    url(r"^grids/", include("grid.urls")),
    url(r"^feeds/", include("feeds.urls")),

    url(r"^categories/(?P<slug>[-\w]+)/$", category, name="category"),
    url(r"^categories/$", homepage, name="categories"),
    url(r"^python3/$", py3_compat, name="py3_compat"),

    url(regex=r'^login/$', view=TemplateView.as_view(template_name='pages/login.html'), name='login',),
    url(r'^logout/$', 'django.contrib.auth.views.logout', {'next_page': '/'}, 'logout',),

    # static pages
    url(r"^about/$", TemplateView.as_view(template_name='pages/faq.html'), name="about"),
    url(r"^terms/$", TemplateView.as_view(template_name='pages/terms.html'), name="terms"),
    url(r"^faq/$", TemplateView.as_view(template_name='pages/faq.html'), name="faq"),
    url(r"^syndication/$", TemplateView.as_view(template_name='pages/syndication.html'), name="syndication"),
    url(r"^contribute/$", TemplateView.as_view(template_name='pages/contribute.html'), name="contribute"),
    url(r"^help/$", TemplateView.as_view(template_name='pages/help.html'), name="help"),

    # new apps
    url(r"^search/", include("searchv2.urls")),

    # apiv2
    url(r'^api/v2/', include('core.apiv2', namespace="apiv2")),

    # apiv3
    url(r'^api/v3/', include('apiv3.urls', namespace="apiv3")),

    # reports
    # url(r'^reports/', include('reports.urls', namespace='reports')),
)

from apiv1.api import Api
from apiv1.resources import (
                    GotwResource, DpotwResource,
                    PackageResource, CategoryResource,
                    GridResource, UserResource
                    )

v1_api = Api()
v1_api.register(PackageResource())
v1_api.register(CategoryResource())
v1_api.register(GridResource())
v1_api.register(GotwResource())
v1_api.register(DpotwResource())
v1_api.register(UserResource())

urlpatterns += patterns('',
    url(r"^api/", include(v1_api.urls)),
)


urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

