from django.db import models
from django.utils.translation import ugettext_lazy as _

from core.models import BaseModel


ITEM_TYPE_CHOICES = (
    ('package', 'Package'),
    ('grid', 'Grid'),    
    
)

class SearchV2(BaseModel):
    """
        Searches available on:
        
            title
            description
            grids
            pacakges
            categories
            number of watchers
            number of forks
            last repo commit
            last release on PyPI
    """
        
    weight          = models.IntegerField(_("Weight"), default=0)
    item_type       = models.CharField(_("Item Type"), max_length=40, choices=ITEM_TYPE_CHOICES)
    title           = models.CharField(_("Title"), max_length="100")
    title_no_prefix = models.CharField(_("No Prefix Title"), max_length="100")
    slug            = models.SlugField(_("Slug"))
    slug_no_prefix  = models.SlugField(_("No Prefix Slug"))
    clean_title     = models.CharField(_("Clean title with no crud"), max_length="100")
    description     = models.TextField(_("Repo Description"), blank=True)    
    category        = models.CharField(_("Category"), blank=True, max_length=50)
    absolute_url    = models.CharField(_("Absolute URL"), max_length="255")
    repo_watchers   = models.IntegerField(_("repo watchers"), default=0)    
    repo_forks      = models.IntegerField(_("repo forks"), default=0)
    pypi_downloads  = models.IntegerField(_("Pypi downloads"), default=0)    
    usage           = models.IntegerField(_("Number of users"), default=0)    
    participants    = models.TextField(_("Participants"),
                        help_text="List of collaborats/participants on the project", blank=True)
    last_committed  = models.DateTimeField(_("Last commit"), blank=True, null=True)
    last_released   = models.DateTimeField(_("Last release"), blank=True, null=True)
    
    class Meta:
        ordering = ['-weight',]
        verbose_name_plural = 'SearchV2s'

    def __unicode__(self):
        return "{0}:{1}".format(self.weight, self.title)
    
    @models.permalink
    def get_absolute_url(self):
        return self.absolute_url
    
    