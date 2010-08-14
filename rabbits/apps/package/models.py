import re
from urllib import urlopen

from django.contrib.auth.models import User
from django.db import models 
from django.utils.translation import ugettext_lazy as _ 

from github2.client import Github
from django_extensions.db.fields import CreationDateTimeField, ModificationDateTimeField 

downloads_re = re.compile(r'<td style="text-align: right;">[0-9]{1,}</td>')

class BaseModel(models.Model): 
    """ Base abstract base class to give creation and modified times """
    created     = CreationDateTimeField(_('created'))
    modified    = ModificationDateTimeField(_('modified'))

    class Meta: 
        abstract = True 

REPO_CHOICES = (
    ('github', 'Github',),
    #('bitbucket', 'bitbucket',),
    #('code.google.com', 'code.google.com', ),
)

class Package(BaseModel):
    
    title           = models.CharField(_("Title"), max_length="100")
    slug            = models.SlugField(_("Slug"))
    repo            = models.CharField(_("Repo"), max_length="50", choices=REPO_CHOICES)
    repo_url        = models.URLField(_("repo URL"))
    repo_watchers   = models.IntegerField(_("repo watchers"), default=0)
    repo_forks      = models.IntegerField(_("repo forks"), default=0)
    pypi_url        = models.URLField(_("pypi URL"))
    pypi_version    = models.CharField(_("Current Pypi version"), max_length="20")    
    pypi_downloads  = models.IntegerField(_("Pypi downloads"), default=0)
    related_packages    = models.ManyToManyField("self", blank=True)
    project_owners      = models.ManyToManyField(User, blank=True, related_name="project_owners")    
    project_committers  = models.ManyToManyField(User, blank=True, related_name="project_committers")
    
    def save(self, *args, **kwargs):
        
        # Get the downloads from pypi
        # TODO - handle when version is added or not
        page = urlopen(self.pypi_url)
        page = page.read()
        match = downloads_re.search(page).group()
        if match:
            self.pypi_downloads = match.replace('<td style="text-align: right;">', '')
            self.pypi_downloads = self.pypi_downloads.replace('</td>', '')
            self.pypi_downloads = int(self.pypi_downloads)
        else:
            self.pypi_downloads = 0
            
        # Get the repo watchers number
        # TODO - make this abstracted so we can plug in other repos
        github = Github()
        repo_name = self.repo_url.replace('http://github.com/','')
        repo = github.repos.show(repo_name)
        self.repo_watchers = repo.watchers
        self.repo_forks = repo.forks        
        
        super(Package, self).save(*args, **kwargs) # Call the "real" save() method.
                    
    def __unicode__(self):
        
        return self.title
    
class PackageExample(BaseModel):
    
    package      = models.ForeignKey(Package)
    title        = models.CharField(_("Title"), max_length="100")
    url          = models.URLField(_("Repo URL"))
    active       = models.BooleanField(_("Active"), default=False, help_text="Moderators have to approve links before they are provided")

    def __unicode__(self):    
        return self.title