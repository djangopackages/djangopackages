"""
This is where GitHub specific models will go
"""

from core.models import BaseModel

class GitHubRepo(BaseModel):
    
    description = models.TextField(_("Repo Description"), blank=True)
    url = models.URLField(_("repo URL"), help_text=url_help_text, blank=True, unique=True, verify_exists=True)
    watchers = models.IntegerField(_("repo watchers"), default=0)
    forks = models.IntegerField(_("repo forks"), default=0)
    
    def __unicode__(self):
        return self.url
