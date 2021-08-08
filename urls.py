from django.conf import settings
from django.conf.urls import include
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, re_path
from django.views.generic.base import TemplateView

from core.apiv1 import apiv1_gone
from homepage.views import homepage, error_404_view, error_500_view, health_check_view, SitemapView
from package.views import category, python3_list
from profiles.views import LogoutView

admin.autodiscover()

urlpatterns = [

    # url(r'^login/\{\{item\.absolute_url\}\}/', RedirectView.as_view(url="/login/github/")),
    path('auth/', include('social_django.urls', namespace='social')),
    # url('', include('social_auth.urls')),
    path('', homepage, name="home"),
    path('health_check/', health_check_view, name="health_check"),
    path('404', error_404_view, name="404"),
    path('500', error_500_view, name="500"),
    re_path(settings.ADMIN_URL_BASE, admin.site.urls),
    path('profiles/', include("profiles.urls")),
    path('packages/', include("package.urls")),
    path('grids/', include("grid.urls")),
    path('feeds/', include("feeds.urls")),

    path('categories/<slug:slug>/', category, name="category"),
    path('categories/', homepage, name="categories"),
    path('python3/', python3_list, name="py3_compat"),

    # url(regex=r'^login/$', view=TemplateView.as_view(template_name='pages/login.html'), name='login',),
    path('logout/', LogoutView.as_view(), name='logout'),

    # static pages
    path('about/', TemplateView.as_view(template_name='pages/faq.html'), name="about"),
    path('terms/', TemplateView.as_view(template_name='pages/terms.html'), name="terms"),
    path('faq/', TemplateView.as_view(template_name='pages/faq.html'), name="faq"),
    path('syndication/', TemplateView.as_view(template_name='pages/syndication.html'), name="syndication"),
    path('help/', TemplateView.as_view(template_name='pages/help.html'), name="help"),
    re_path(r"^sitemap\.xml$", SitemapView.as_view(), name="sitemap"),

    # new apps
    path('search/', include("searchv2.urls")),

    # apiv2
    # url(r'^api/v2/', include('core.apiv2', namespace="apiv2")),

    # apiv3
    path('api/v3/', include('apiv3.urls', namespace="apiv3")),

    # apiv4
    path('api/v4/', include("apiv4.urls", namespace='apiv4')),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),

    re_path(
        r"^api/v1/.*$", view=apiv1_gone,
        name="apiv1_gone",
    ),

    # url(r'^api/v1/', include('core.apiv1', namespace="apitest")),

    # reports
    # url(r'^reports/', include('reports.urls', namespace='reports')),
]


urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
