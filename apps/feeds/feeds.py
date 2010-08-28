from django.contrib.syndication.views import Feed
from django.utils.feedgenerator import Atom1Feed
from package.models import Package

class RssLatestPackagesFeed(Feed):
    title = "Latest Django packages added"
    link = "/packages/latest"
    description = "The last 15 packages added"

    def items(self):
        return Package.objects.all().order_by("-created")[:15]

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return item.repo_description
        
    def item_pubdate(self, item):
        return item.created
        
class AtomLatestPackagesFeed(RssLatestPackagesFeed):
    feed_type = Atom1Feed
    subtitle = RssLatestPackagesFeed.description
    
class RssLatestFeed(Feed):
    title = "Last 15 things to happen"
    link  = ""
    description = "An aggregation of package, grid and blog entries"