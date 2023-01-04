from django.db import models
from django.utils.translation import gettext_lazy as _
from django_better_admin_arrayfield.models.fields import ArrayField

from core.models import BaseModel


class Classifier(BaseModel):
    classifier = models.TextField()
    active = models.BooleanField(
        _("Active"),
        default=True,
    )
    tags = ArrayField(models.CharField(max_length=100), blank=True, null=True)

    class Meta:
        ordering = ["classifier"]
        verbose_name_plural = "Classifiers"

    def __str__(self):
        return f"{self.classifier}"
