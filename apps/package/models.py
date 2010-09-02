# TODO - cleanup regex to do proper string subs
# TODO - add is_other field to repo
# TODO - add repo.user_url

import logging
import os
import re
import sys
from urllib import urlopen

from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db import models
from django.utils.translation import ugettext_lazy as _

from github2.client import Github

from package.handlers import github

from package.fields import CreationDateTimeField, ModificationDateTimeField

from package.utils import uniquer

class NoPyPiVersionFound(Exception):
    pass

class BaseModel(models.Model):
    """ Base abstract base class to give creation and modified times """
    created     = CreationDateTimeField(_('created'))
    modified    = ModificationDateTimeField(_('modified'))
    
    class Meta:
        abstract = True

class Category(BaseModel):
    
    title = models.CharField(_("Title"), max_length="50")
    slug  = models.SlugField(_("slug"))
    description = models.TextField(_("description"), blank=True)
    title_plural = models.CharField(_("Title Plural"), max_length="50", blank=True)    
    
    class Meta:
        ordering = ['title']
        verbose_name_plural = 'Categories'
    
    def __unicode__(self):
        return self.title
        
REPO_CHOICES = (
    ("package.handlers.unsupported", "Unsupported"),
    ("package.handlers.bitbucket", "Bitbucket"),
    ("package.handlers.github", "Github")
)

class Repo(BaseModel):
    
    is_supported = models.BooleanField(_("Supported?"), help_text="Does Django Packages support this repo site?", default=False)
    title        = models.CharField(_("Title"), max_length="50")
    description  = models.TextField(_("description"), blank=True)
    url          = models.URLField(_("base URL of repo"))
    is_other     = models.BooleanField(_("Is Other?"), default=False, help_text="Only one can be set this way")
    user_regex   = models.CharField(_("User Regex"), help_text="Regex to calculate user's name or id",max_length="100", blank=True)
    repo_regex   = models.CharField(_("Repo Regex"), help_text="Regex to get repo's name", max_length="100", blank=True)
    slug_regex   = models.CharField(_("Slug Regex"), help_text="Regex to get repo's slug", max_length="100", blank=True)    
    handler      = models.CharField(_("Handler"), 
        help_text="Warning: Don't change this unless you know what you are doing!", 
        choices=REPO_CHOICES,
        max_length="200",
        default="package.handlers.unsupported")
    
    class Meta:
        ordering = ['-is_supported', 'title']
    
    def __unicode__(self):
        if not self.is_supported:
            return '%s (unsupported)' % self.title
        
        return self.title

downloads_re = re.compile(r'<td style="text-align: right;">[0-9]{1,}</td>')
doap_re      = re.compile(r"/pypi\?\:action=doap\&amp;name=[a-zA-Z0-9\.\-\_]+\&amp;version=[a-zA-Z0-9\.\-\_]+")
version_re   = re.compile(r'<revision>[a-zA-Z0-9\.\-\_]+</revision>')

repo_url_help_text = "Enter your project repo hosting URL here.<br />Example: http://bitbucket.com/ubernostrum/django-registration"
pypi_url_help_text = "<strong>Leave this blank if this package does not have a PyPI release.</strong><br />What PyPI uses to index your package. <br />Example: django-registration"

class Package(BaseModel):
    
    title           = models.CharField(_("Title"), max_length="100")
    slug            = models.SlugField(_("Slug"), help_text="Slugs will be lowercased", unique=True)
    category        = models.ForeignKey(Category)
    repo            = models.ForeignKey(Repo, null=True)
    repo_description= models.TextField(_("Repo Description"), blank=True)
    repo_url        = models.URLField(_("repo URL"), help_text=repo_url_help_text, blank=True)
    repo_watchers   = models.IntegerField(_("repo watchers"), default=0)
    repo_forks      = models.IntegerField(_("repo forks"), default=0)
    repo_commits    = models.IntegerField(_("repo commits"), default=0)
    pypi_url        = models.URLField(_("PyPI slug"), help_text=pypi_url_help_text, blank=True, default='')
    pypi_version    = models.CharField(_("Current Pypi version"), max_length="20", blank=True)
    pypi_downloads  = models.IntegerField(_("Pypi downloads"), default=0)
    related_packages    = models.ManyToManyField("self", blank=True)
    participants    = models.TextField(_("Participants"),
                        help_text="List of collaborats/participants on the project", blank=True)
    usage           = models.ManyToManyField(User, blank=True)
                        
    
    def active_examples(self):
        return self.packageexample_set.filter(active=True)
    
    def grids(self):
        
        return (x.grid for x in self.gridpackage_set.all())
    
    def repo_name(self):
        return self.repo_url.replace(self.repo.url + '/','')
    
    def participant_list(self):
        
        return self.participants.split(',')
    
    def save(self, *args, **kwargs):
        
        # Get the downloads from pypi
        if self.pypi_url.strip() and self.pypi_url != "http://pypi.python.org/pypi/":
            
            page = urlopen(self.pypi_url).read()
            # If the target page is an Index of packages
            if 'Index of Packages' in page:
                if self.pypi_url.endswith('/'):
                    project_name = self.pypi_url[:-1]
                else:
                    project_name = self.pypi_url
                project_name = os.path.split(project_name)[1]
                logging.debug(project_name)
                page_re = re.compile(r'<a href="/pypi/%s/([a-zA-Z0-9\.\-\_]{1,})">' % project_name)
                match = page_re.search(page).group()
                if match:
                    url = match.replace('<a href="', 'http://pypi.python.org')
                    url = url.replace('">', '')
                    page = urlopen(url).read()
                else:
                    raise NoPyPiVersionFound('self.pypi_url')
            
            # We have a working page so grab the package info
            match = downloads_re.search(page)
            if match:
                match = match.group()
                self.pypi_downloads = match.replace('<td style="text-align: right;">', '')
                self.pypi_downloads = self.pypi_downloads.replace('</td>', '')
                self.pypi_downloads = int(self.pypi_downloads)
            else:
                # TODO - This could actually be that they don't show downloads.
                #       For example, Pinax does this. Deal with this somehow when not so late
                self.pypi_downloads = 0
            
            # get the version off of Pypi doap
            match = doap_re.search(page)
            if match:
                group = match.group()
                if group:
                    url = 'http://pypi.python.org%s' % group
                    doap = urlopen(url).read()
                    match = version_re.search(doap).group()
                    self.pypi_version = match.replace('<revision>','').replace('</revision>','')
            
        
        # Get the repo watchers number
        # TODO - make this abstracted so we can plug in other repos
        base_handler = __import__(self.repo.handler)
        handler = sys.modules[self.repo.handler]

        self = handler.pull(self)
        

        
        super(Package, self).save(*args, **kwargs) # Call the "real" save() method.

    
    class Meta:
        ordering = ['title']
    
    def __unicode__(self):
        
        return self.title
        
    @models.permalink
    def get_absolute_url(self):
        return ("package", [self.slug])
        

class PackageExample(BaseModel):
    
    package      = models.ForeignKey(Package)
    title        = models.CharField(_("Title"), max_length="100")
    url          = models.URLField(_("URL"))
    active       = models.BooleanField(_("Active"), default=True, help_text="Moderators have to approve links before they are provided")
    
    class Meta:
        ordering = ['title']
    
    def __unicode__(self):
        return self.title

class Commit(BaseModel):
    
    package      = models.ForeignKey(Package)
    commit_date  = models.DateTimeField(_("Commit Date"))
    
    class Meta:
        ordering = ['-commit_date']
        
    def __unicode__(self):
        return "Commit for '%s' on %s" % (self.package.title, unicode(self.commit_date))