from django.contrib.sitemaps import Sitemap
from .models import Post


class BlogSitemap(Sitemap):
    changefreq = "never"
    priority = 0.7

    def items(self):
        return Post.objects.published().order_by("-published_date")

    def lastmod(self, obj):
        return obj.modified
