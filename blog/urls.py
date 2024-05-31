from django.urls import path

from blog import feeds
from blog import views

urlpatterns = [
    path("", views.PostList.as_view(), name="post_list"),
    path("feeds/", feeds.PostFeed(), name="post_feed"),
    path("feeds/atom/", feeds.PostAtomFeed(), name="post_atom_feed"),
    path("feeds/rss/", feeds.PostFeed(), name="post_rss_feed"),
    path("<slug:slug>/", views.PostDetail.as_view(), name="post_detail"),
]
