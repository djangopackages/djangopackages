from __future__ import annotations

from django.db import models


class PostQuerySet(models.QuerySet):
    def active(self):
        return self.exclude(published_date__isnull=True)

    def detail(self):
        return self.defer(None)

    def list(self):
        return self.defer("content")


class PostManager(models.Manager):
    def get_queryset(self):
        return PostQuerySet(self.model, using=self._db)

    def active(self):
        return self.get_queryset().active()

    def detail(self):
        return self.get_queryset().detail()

    def list(self):
        return self.get_queryset().list()
