from django.contrib.syndication.views import Feed
from package.models import Package

class LatestPackagesFeed(Feed):
    title = "Latest Django packages added"
    link = "/packages/latest"
    description = "The last 15 packages added"

    def items(self):
        return Package.objects.all()[:15]

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return item.repo_description