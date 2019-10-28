from django.conf import settings
from django.conf.urls import url, include
from django.conf.urls.static import static
from django.views.generic.base import TemplateView, RedirectView

from django.contrib import admin
admin.autodiscover()

from core.apiv1 import apiv1_gone
from homepage.views import homepage, error_404_view, error_500_view, health_check_view, SitemapView
from package.views import category, python3_list

from profiles.views import LogoutView

urlpatterns = [

    # url(r'^login/\{\{item\.absolute_url\}\}/', RedirectView.as_view(url="/login/github/")),
    url('^auth/', include('social_django.urls', namespace='social')),
    # url('', include('social_auth.urls')),
    url(r"^$", homepage, name="home"),
    url(r"^health_check/$", health_check_view, name="health_check"),
    url(r"^404$", error_404_view, name="404"),
    url(r"^500$", error_500_view, name="500"),
    url(settings.ADMIN_URL_BASE, admin.site.urls),
    url(r"^profiles/", include("profiles.urls")),
    url(r"^packages/", include("package.urls")),
    url(r"^grids/", include("grid.urls")),
    url(r"^feeds/", include("feeds.urls")),

    url(r"^categories/(?P<slug>[-\w]+)/$", category, name="category"),
    url(r"^categories/$", homepage, name="categories"),
    url(r"^python3/$", python3_list, name="py3_compat"),

    # url(regex=r'^login/$', view=TemplateView.as_view(template_name='pages/login.html'), name='login',),
    url(r'^logout/$', LogoutView, {'next_page': '/'}, 'logout',),

    # static pages
    url(r"^about/$", TemplateView.as_view(template_name='pages/faq.html'), name="about"),
    url(r"^terms/$", TemplateView.as_view(template_name='pages/terms.html'), name="terms"),
    url(r"^faq/$", TemplateView.as_view(template_name='pages/faq.html'), name="faq"),
    url(r"^syndication/$", TemplateView.as_view(template_name='pages/syndication.html'), name="syndication"),
    url(r"^help/$", TemplateView.as_view(template_name='pages/help.html'), name="help"),
    url(r"^sitemap\.xml$", SitemapView.as_view(), name="sitemap"),

    # new apps
    url(r"^search/", include("searchv2.urls")),

    # apiv2
    # url(r'^api/v2/', include('core.apiv2', namespace="apiv2")),

    # apiv3
    url(r'^api/v3/', include('apiv3.urls', namespace="apiv3")),

    # apiv4
    url(r'^api/v4/', include("apiv4.urls", namespace='apiv4')),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),

    url(
        regex=r"^api/v1/.*$",
        view=apiv1_gone,
        name="apiv1_gone",
    ),

    # url(r'^api/v1/', include('core.apiv1', namespace="apitest")),

    # reports
    # url(r'^reports/', include('reports.urls', namespace='reports')),
]


urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
