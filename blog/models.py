from html import unescape

from django.db import models
from django.urls import reverse
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
        # If the post is being published for the first time, generate a slug
        if self.published_date and not self.slug:
            # Format the published_date to include only the date portion
            date_str = self.published_date.strftime("%Y-%m-%d")
            self.slug = slugify(f"{date_str}-{self.title}")

        super().save(*args, **kwargs)

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
