from django.contrib.sitemaps import Sitemap
from .models import Grid


class GridSitemap(Sitemap):
    changefreq = "daily"
    priority = 1.0

    def items(self):
        return Grid.objects.all()

    def lastmod(self, obj):
        return obj.modified
