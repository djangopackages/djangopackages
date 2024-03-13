"""url patterns for the feeds"""

from django.urls import path

from .feeds import AtomLatestPackagesFeed, RssLatestPackagesFeed

urlpatterns = [
    path(
        "packages/latest/rss/",
        RssLatestPackagesFeed(),
        name="feeds_latest_packages_rss",
    ),
    path(
        "packages/latest/atom/",
        AtomLatestPackagesFeed(),
        name="feeds_latest_packages_atom",
    ),
]
