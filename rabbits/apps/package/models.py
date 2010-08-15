# TODO - cleanup regex to do proper string subs

import logging
import os
import re
from urllib import urlopen

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models 
from django.utils.translation import ugettext_lazy as _ 

from django_extensions.db.fields import CreationDateTimeField, ModificationDateTimeField 
from github2.client import Github

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
    description = models.TextField(_("Participants"), blank=True)

    class Meta:
        ordering = ['title']
        verbose_name_plural = 'Categories'

    def __unicode__(self):
        return self.title
        
class Repo(BaseModel):
    
    title = models.CharField(_("Title"), max_length="50")
    description = models.TextField(_("description"), blank=True)
    url = models.URLField(_("base URL of repo"))
    
    def __unicode__(self):
        
        return self.title

downloads_re = re.compile(r'<td style="text-align: right;">[0-9]{1,}</td>')
doap_re      = re.compile(r"/pypi\?\:action=doap\&amp;name=[a-zA-Z0-9\.\-\_]+\&amp;version=[a-zA-Z0-9\.\-\_]+")
version_re   = re.compile(r'<revision>[a-zA-Z0-9\.\-\_]+</revision>')

class Package(BaseModel):
    
    title           = models.CharField(_("Title"), max_length="100")
    slug            = models.SlugField(_("Slug"))
    category        = models.ForeignKey(Category)
    repo            = models.ForeignKey(Repo)
    repo_description= models.TextField(_("Repo Description"), blank=True)
    repo_url        = models.URLField(_("repo URL"))
    repo_watchers   = models.IntegerField(_("repo watchers"), default=0)
    repo_forks      = models.IntegerField(_("repo forks"), default=0)
    pypi_url        = models.URLField(_("pypi URL"), blank=True)
    pypi_version    = models.CharField(_("Current Pypi version"), max_length="20", blank=True)    
    pypi_downloads  = models.IntegerField(_("Pypi downloads"), default=0)
    related_packages    = models.ManyToManyField("self", blank=True)
    participants    = models.TextField(_("Participants"), 
                        help_text="List of collaborats/participants on the project", blank=True)
                        
    def active_examples(self):
        return self.packageexample_set.filter(active=True)
        
    def grids(self):
        
        return (x.grid for x in self.gridpackage_set.all())
    
    def repo_name(self):
        # TODO make work under other repos
        return self.repo_url.replace('http://github.com/','')
                        
    def participant_list(self):
        
        return self.participants.split(',')
    
    def save(self, *args, **kwargs):
        
        # Get the downloads from pypi
        # TODO - handle when version is added or not
        if self.pypi_url:
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
            match = downloads_re.search(page).group()
            if match:
                self.pypi_downloads = match.replace('<td style="text-align: right;">', '')
                self.pypi_downloads = self.pypi_downloads.replace('</td>', '')
                self.pypi_downloads = int(self.pypi_downloads)
            else:
                self.pypi_downloads = 0
            
            # get the version off of Pypi doap
            match = doap_re.search(page).group()
            if match:
                url = 'http://pypi.python.org%s' % match
                doap = urlopen(url).read()
                match = version_re.search(doap).group()
                self.pypi_version = match.replace('<revision>','').replace('</revision>','')
            
            
        # Get the repo watchers number
        # TODO - make this abstracted so we can plug in other repos
        github   = Github()
        repo_name = self.repo_name()
        repo         = github.repos.show(repo_name)
        self.repo_watchers    = repo.watchers # set watchers
        self.repo_forks       = repo.forks # set fork
        self.repo_description = repo.description


        collaborators = github.repos.list_collaborators(repo_name)
        if collaborators:
            self.participants = ','.join(collaborators)
        
        super(Package, self).save(*args, **kwargs) # Call the "real" save() method.
        
        # get committers

    class Meta:
        ordering = ['title']    
                    
    def __unicode__(self):
        
        return self.title
    
class PackageExample(BaseModel):
    
    package      = models.ForeignKey(Package)
    title        = models.CharField(_("Title"), max_length="100")
    url          = models.URLField(_("URL"))
    active       = models.BooleanField(_("Active"), default=True, help_text="Moderators have to approve links before they are provided")
    
    class Meta:
        ordering = ['title']    

    def __unicode__(self):    
        return self.title