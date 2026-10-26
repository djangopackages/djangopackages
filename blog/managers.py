from __future__ import annotations

from django.db import models
from django.utils import timezone


class PostQuerySet(models.QuerySet):
    def published(self):
        """Posts the public may see: published, and the publish date has arrived."""
        from blog.models import Post

        return self.filter(
            status=Post.Status.PUBLISHED,
            published_date__lte=timezone.now(),
        )

    def detail(self):
        return self.defer(None)

    def list(self):
        return self.defer("content")


class PostManager(models.Manager):
    def get_queryset(self):
        return PostQuerySet(self.model, using=self._db)

    def published(self):
        return self.get_queryset().published()

    def detail(self):
        return self.get_queryset().detail()

    def list(self):
        return self.get_queryset().list()
