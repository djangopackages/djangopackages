from django.db import models
from django.utils.text import slugify

from core.models import BaseModel


class Post(BaseModel):
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
