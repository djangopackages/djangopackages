"""Contains classes for the feeds"""

from django.conf import settings
from django.contrib.syndication.views import Feed
from django.utils.feedgenerator import Atom1Feed

from package.models import Package


class RssLatestPackagesFeed(Feed):
    """RSS Feed for the packages"""
    title = "Latest {0} packages added".format(settings.FRAMEWORK_TITLE)
    link = "/packages/latest/"
    description = "The last 15 packages added"

    def items(self):
        """Returns 15 most recently created repositories"""
        return Package.objects.all().order_by("-created")[:15]

    def item_title(self, item):
        """Get title of the repository"""
        return item.title

    def item_description(self, item):
        """Get description of the repository"""
        return item.repo_description

    def item_pubdate(self, item):
        """Get publication date"""
        return item.created


class AtomLatestPackagesFeed(RssLatestPackagesFeed):
    """Atom feed for the packages"""
    feed_type = Atom1Feed
    subtitle = RssLatestPackagesFeed.description
