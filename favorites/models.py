from django.db import models
from django.contrib.auth.models import User
from core.models import BaseModel
from package.models import Package


class Favorite(BaseModel):
    favorited_by = models.ForeignKey(
        User, blank=True, null=True, on_delete=models.SET_NULL
    )
    package = models.ForeignKey(Package, on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.package.favorite_count += 1
        self.package.save()

    def delete(self, *args, **kwargs):
        self.package.favorite_count -= 1
        self.package.save()
        super().delete(*args, **kwargs)
