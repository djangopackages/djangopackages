from django.contrib.sitemaps import Sitemap
from django.urls import reverse


class StaticViewSitemap(Sitemap):
    priority = 0.8
    changefreq = "weekly"

    def items(self):
        return [
            "home",
            "about",
            "terms",
            "faq",
            "stack",
            "open",
            "help",
            "funding",
        ]

    def location(self, item):
        return reverse(item)
