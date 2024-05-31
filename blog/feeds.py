from __future__ import annotations

from django.contrib.syndication.views import Feed
from django.utils.feedgenerator import Atom1Feed
from markdown_it import MarkdownIt

from .models import Post


class PostFeed(Feed):
    title = "Django Packages: Changelogs"
    link = "/"
    description = (
        "Latest Django Packages Changelogs posted at https://djangopackages.org"
    )

    def author_name(self):
        return "Django Packages"

    def items(self):
        queryset = Post.objects.active().order_by("-published_date")
        return queryset[:10]

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        md = MarkdownIt()
        return md.render(item.content)

    def item_link(self, item):
        return item.get_absolute_url()

    def item_updateddate(self, item):
        return item.published_date


class PostAtomFeed(PostFeed):
    feed_type = Atom1Feed
