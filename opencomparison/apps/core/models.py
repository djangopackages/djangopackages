from django.db import models
from django.utils.translation import ugettext_lazy as _

from core.fields import CreationDateTimeField, ModificationDateTimeField

class BaseModel(models.Model):
    """ Base abstract base class to give creation and modified times """
    created     = CreationDateTimeField(_('created'))
    modified    = ModificationDateTimeField(_('modified'))
    

    class Meta:
        abstract = True

