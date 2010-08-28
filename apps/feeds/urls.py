from django.conf.urls.defaults import *

from feeds import *

urlpatterns = patterns("",
    (r'^packages/latest/rss/$', RssLatestPackagesFeed()),
    (r'^packages/latest/atom/$', AtomLatestPackagesFeed()),    
)