from html import unescape

from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.html import strip_tags
from django.utils.text import Truncator, slugify
from markdown_it import MarkdownIt

from blog.managers import PostManager
from core.models import BaseModel


class Post(BaseModel):
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"

    title = models.CharField(max_length=200)
    slug = models.SlugField(
        blank=True,
        max_length=250,
        null=True,
        unique_for_date="published_date",
    )
    content = models.TextField()
    author = models.CharField(blank=True, max_length=200, null=True)
    published_date = models.DateTimeField(blank=True, null=True)
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.DRAFT,
    )

    objects = PostManager()

    class Meta:
        ordering = ["-published_date"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        # A post needs a slug before it is published so staff can preview
        # it at its URL (#1799). Dated slugs are kept for posts that are
        # published on first save, matching the older posts.
        if not self.slug:
            if self.published_date:
                date_str = self.published_date.strftime("%Y-%m-%d")
                self.slug = slugify(f"{date_str}-{self.title}")
            else:
                self.slug = slugify(self.title)

        super().save(*args, **kwargs)

    @property
    def is_public(self) -> bool:
        """Published, and the publish date has arrived."""
        return (
            self.status == self.Status.PUBLISHED
            and self.published_date is not None
            and self.published_date <= timezone.now()
        )

    def get_absolute_url(self):
        return reverse("post_detail", args=[self.slug])

    def get_opengraph_image_url(self):
        return reverse("post_opengraph", args=[self.slug])

    @property
    def summary(self):
        """The opening of the post, as plain text for a card or a meta tag.

        Posts are Markdown, so it has to be rendered before the tags come
        off. Stripping the raw source instead leaves the syntax behind, and
        "**djangopackages.org**" ends up on the social card with its
        asterisks showing.
        """
        html = MarkdownIt("gfm-like", {"linkify": True}).render(self.content)
        text = " ".join(unescape(strip_tags(html)).split())
        return Truncator(text).chars(130)


class PostImage(BaseModel):
    """An image an author uploads to embed in a Post's Markdown content.

    The admin shows a ready-to-paste `![](url)` snippet; the author drops it
    into a post's `content`, where the `markdown` filter renders it as `<img>`.
    """

    image = models.ImageField(upload_to="blog/")

    def __str__(self):
        return self.image.name

    @property
    def markdown(self):
        if not self.image:
            return ""
        # ty: ignore[unresolved-attribute] — ImageField returns a FieldFile with .url
        return f"![]({self.image.url})"
