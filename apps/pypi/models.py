from django.db import models
from django.utils.translation import ugettext_lazy as _

from core.models import BaseModel
from package.models import Package

class PypiUpdateLog(BaseModel):
    
    last_update_success = models.BooleanField(_("Last Update Success"), default=False)
    
    class Meta:
        ordering = ('modified',)
        get_latest_by = ('modified',)
        verbose_name = u"PyPI Update Log"
        verbose_name_plural = u"PyPI Update Logs"
        
    def __unicode__(self):
        return "PyPI Update at " + unicode(self.modified)
    
    @classmethod
    def last_update(cls):
        try:
            last = cls.objects.latest()
            return last.modified
        except PypiUpdateLog.DoesNotExist:
            return None