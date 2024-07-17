from django.db import models
from django.contrib.auth.models import User
from core.models import BaseModel
from package.models import Package

# Create your models here.


class Favourite(BaseModel):
    favourited_by = models.ForeignKey(
        User, blank=True, null=True, on_delete=models.SET_NULL
    )
    package = models.ForeignKey(Package, on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.package.favourite_count += 1
        self.package.save()

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)
        self.package.favourite_count -= 1
        self.package.save()
