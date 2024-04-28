from django.contrib.sitemaps import Sitemap
from .models import Package


class PackageSitemap(Sitemap):
    changefreq = "daily"
    priority = 1.0

    def items(self):
        return Package.objects.active()

    def lastmod(self, obj):
        return obj.modified
