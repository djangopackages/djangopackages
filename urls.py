from django.conf import settings
from django.urls import include
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, re_path
from django.views.generic.base import TemplateView

from core import __version__
from core.apiv1 import apiv1_gone
from homepage.views import (
    homepage,
    error_404_view,
    error_500_view,
    health_check_view,
    OpenView,
    SitemapView,
)
from package.views import PackageByCategoryListView, PackagePython3ListView
from profiles.views import LogoutView

admin_header = f"Django Packages v{__version__}"
admin.site.enable_nav_sidebar = False  # disabled until Django 3.x
admin.site.site_header = admin_header
admin.site.site_title = admin_header

urlpatterns = [
    # url(r'^login/\{\{item\.absolute_url\}\}/', RedirectView.as_view(url="/login/github/")),
    path("auth/", include("social_django.urls", namespace="social")),
    # url('', include('social_auth.urls')),
    path("", homepage, name="home"),
    path("health_check/", health_check_view, name="health_check"),
    path("404", error_404_view, name="404"),
    path("500", error_500_view, name="500"),
    re_path(settings.ADMIN_URL_BASE, admin.site.urls),
    path("profiles/", include("profiles.urls")),
    path("packages/", include("package.urls")),
    path("grids/", include("grid.urls")),
    path("feeds/", include("feeds.urls")),
    path(
        "categories/<slug:slug>/", PackageByCategoryListView.as_view(), name="category"
    ),
    path("categories/", homepage, name="categories"),
    path("python3/", PackagePython3ListView.as_view(), name="py3_compat"),
    # url(regex=r'^login/$', view=TemplateView.as_view(template_name='pages/login.html'), name='login',),
    path("logout/", LogoutView.as_view(), name="logout"),
    # static pages
    path("about/", TemplateView.as_view(template_name="pages/faq.html"), name="about"),
    path(
        "terms/", TemplateView.as_view(template_name="pages/terms.html"), name="terms"
    ),
    path("faq/", TemplateView.as_view(template_name="pages/faq.html"), name="faq"),
    path("open/", OpenView.as_view(), name="open"),
    path(
        "syndication/",
        TemplateView.as_view(template_name="pages/syndication.html"),
        name="syndication",
    ),
    path("help/", TemplateView.as_view(template_name="pages/help.html"), name="help"),
    path(
        "funding/",
        TemplateView.as_view(template_name="pages/funding.html"),
        name="funding",
    ),
    path("sitemap.xml", SitemapView.as_view(), name="sitemap"),
    # new apps
    path("search/", include("searchv2.urls")),
    # apiv3
    path("api/v3/", include("apiv3.urls", namespace="apiv3")),
    # apiv4
    path("api/v4/", include("apiv4.urls", namespace="apiv4")),
    path("api-auth/", include("rest_framework.urls", namespace="rest_framework")),
    re_path(
        r"^api/v1/.*$",
        view=apiv1_gone,
        name="apiv1_gone",
    ),
    # url(r'^api/v1/', include('core.apiv1', namespace="apitest")),
]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns.append(path("__debug__/", include(debug_toolbar.urls)))

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
