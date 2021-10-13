from django.db import models

from core.fields import CreationDateTimeField, ModificationDateTimeField
from django.utils.translation import gettext_lazy as _


class BaseModel(models.Model):
    """Base abstract base class to give creation and modified times"""

    created = CreationDateTimeField(_("created"))
    modified = ModificationDateTimeField(_("modified"))

    class Meta:
        abstract = True

    def cache_namer(self, method):
        return "{}:{}".format(method.__name__, self.pk)

    def model_cache_name(self):
        return "{}:{}".format(self.__class__.__name__, self.pk)
