from django.conf import settings

from grid.models import Grid
from package.models import Package, Commit, Version
from searchv2.models import SearchV2

"""
_underscore = '%s_%s' % (settings.PACKAGINATOR_SEARCH_PREFIX, q)    
_dash = '%s-%s' % (settings.PACKAGINATOR_SEARCH_PREFIX, q)
_space = '%s %s' % (settings.PACKAGINATOR_SEARCH_PREFIX, q)    
"""

def remove_prefix(value):
    value = value.lower()
    for char in ["_", ",", ".", "-", " ", "/",]:
        value = value.replace("{0}{1}".format(settings.PACKAGINATOR_SEARCH_PREFIX, char), "")
    return value

def build_1():
    
    SearchV2.objects.all().delete()
    for package in Package.objects.all():
        
        obj = SearchV2.objects.create(
            weight=0,
            item_type="package",
            title=package.title,
            title_no_prefix=remove_prefix(package.title),
            slug=package.slug,
            slug_no_prefix=remove_prefix(package.slug),
            description=package.repo_description,
            category=package.category.title,
            absolute_url=package.get_absolute_url(),
            repo_watchers=package.repo_watchers,
            repo_forks=package.repo_forks,
            pypi_downloads=package.pypi_downloads,
            usage=package.usage.count(),
            participants=package.participants,
            #last_released not yet supported
        )
        try:
            obj.last_committed=package.commit_set.latest().commit_date
            obj.save()
        except Commit.DoesNotExist:
            pass
            
    return SearchV2.objects.all()
                    
        
"""  
weight          = models.IntegerField(_("Weight"), default=0)
item_type       = models.CharField(_("Item Type"), max_length=40, choices=ITEM_TYPE_CHOICES)
title           = models.CharField(_("Title"), max_length="100")
title_no_prefix = models.CharField(_("No prefix Title"), max_length="100")
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
"""