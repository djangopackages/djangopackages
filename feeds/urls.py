"""url patterns for the feeds"""

from .feeds import *
from django.urls import path

urlpatterns = [
    path('packages/latest/rss/', RssLatestPackagesFeed(), name="feeds_latest_packages_rss"),
    path('packages/latest/atom/', AtomLatestPackagesFeed(), name="feeds_latest_packages_atom"),
]
