from django.contrib.sitemaps import Sitemap
from django.urls import reverse


class StaticViewSitemap(Sitemap):
    priority = 0.8
    changefreq = "weekly"

    def items(self):
        return ["home", "about", "terms", "faq", "stack", "open", "help", "funding",]

    def location(self, item):
        return reverse(item)

    def get_urls(self, page=1, site=None, protocol=None):
        s = super().get_urls(page, site, protocol)
        print("==========================================")
        print(s)
        return s
