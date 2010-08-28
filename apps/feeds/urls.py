from django.conf.urls.defaults import *

from feeds import LatestPackagesFeed

urlpatterns = patterns("",
    (r'^packages/latest/rss/$', LatestPackagesFeed()),
)