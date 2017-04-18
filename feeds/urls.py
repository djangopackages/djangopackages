"""url patterns for the feeds"""

from django.conf.urls import url

from .feeds import *

urlpatterns = [
    url(r'^packages/latest/rss/$', RssLatestPackagesFeed(), name="feeds_latest_packages_rss"),
    url(r'^packages/latest/atom/$', AtomLatestPackagesFeed(), name="feeds_latest_packages_atom"),
]
