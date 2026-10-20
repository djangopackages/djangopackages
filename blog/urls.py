from django.urls import path
from django.views.decorators.cache import cache_page

from blog import feeds
from blog import views

urlpatterns = [
    path("", views.PostList.as_view(), name="post_list"),
    path("feeds/", feeds.PostFeed(), name="post_feed"),
    path("feeds/atom/", feeds.PostAtomFeed(), name="post_atom_feed"),
    path("feeds/rss/", feeds.PostFeed(), name="post_rss_feed"),
    path(
        "<slug:slug>/opengraph/",
        cache_page(60 * 60 * 24)(views.PostOpenGraphView.as_view()),
        name="post_opengraph",
    ),
    path("<slug:slug>/", views.PostDetail.as_view(), name="post_detail"),
]
