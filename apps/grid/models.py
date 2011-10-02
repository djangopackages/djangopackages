from django.conf import settings
from django.contrib.auth.models import User
from django.core.cache import cache
from django.db import models
from django.utils.translation import ugettext_lazy as _ 

from core.models import BaseModel
from core.utils import cache_fetcher
from grid import cachekeys
from package.models import Package

class Grid(BaseModel):
    """Grid object, inherits form :class:`package.models.BaseModel`. Attributes:

    * :attr:`~grid.models.Grid.title` - grid title
    * :attr:`~grid.models.Grid.slug` - grid slug for SEO
    * :attr:`~grid.models.Grid.description` - description of the grid 
      with line breaks and urlized links
    * :attr:`~grid.models.Grid.is_locked` - boolean field accessible
      to moderators
    * :attr:`~grid.models.Grid.packages` - many-to-many relation 
      with :class:~`grid.models.GridPackage` objects
    """

    title        = models.CharField(_('Title'), max_length=100)
    slug         = models.SlugField(_('Slug'), help_text="Slugs will be lowercased", unique=True)    
    description  = models.TextField(_('Description'), blank=True, help_text="Lines are broken and urls are urlized")
    is_locked    = models.BooleanField(_('Is Locked'), default=False, help_text="Moderators can lock grid access")
    packages     = models.ManyToManyField(Package, through="GridPackage")
    header       = models.BooleanField(_("Header tab?"), default=False, help_text="If checked then displayed on homepage header")
    
    def elements(self):
        elements = []
        for feature in self.feature_set.all(): 
            for element in feature.element_set.all(): 
                elements.append(element)
        return elements
                    
    def __unicode__(self):
        return self.title
    
    @property
    def grid_packages(self):
        """ Gets all the packages and orders them for views and other things
         """
        key, grid_packages = cache_fetcher(cachekeys.grid_grid_packages, self)
        if grid_packages is not None:
            return grid_packages
        gp = self.gridpackage_set.select_related('gridpackage', 'package__repo', 'package__category')
        grid_packages = gp.annotate(usage_count=models.Count('package__usage')).order_by('-usage_count', 'package')
        cache.set(key, grid_packages, settings.CACHE_TIMEOUT)
        return grid_packages
        
    def save(self, *args, **kwargs):
        self.grid_packages # fire the cache
        super(Grid, self).save(*args, **kwargs)

    @models.permalink
    def get_absolute_url(self):
        return ("grid", [self.slug])
        
    class Meta:
        ordering = ['title']

class GridPackage(BaseModel):
    """Grid package.
    This model describes packages listed on one side of the grids
    and
    explicitly defines the many-to-many relationship between grids
    and the packages
    (i.e - allows any given package to be assigned to several grids at once).

    Attributes:

    * :attr:`grid` - the :class:`~apps.grid.models.Grid` to which the package is assigned
    * :attr:`package` - the :class:`~apps.grid.models.Package`
    """
    
    grid        = models.ForeignKey(Grid)
    package     = models.ForeignKey(Package)
    
    class Meta:
        verbose_name = 'Grid Package'
        verbose_name_plural = 'Grid Packages'
        
    def save(self, *args, **kwargs):
        self.grid.grid_packages # fire the cache
        super(GridPackage, self).save(*args, **kwargs)
        
        
    def __unicode__(self):
        return '%s : %s' % (self.grid.slug, self.package.slug)
    
class Feature(BaseModel):
    """ These are the features measured against a grid.
    ``Feature`` has the following attributes:

    * :attr:`grid` - the grid to which the feature is assigned
    * :attr:`title` - name of the feature (100 chars is max)
    * :attr:`description` - plain-text description
    """
    
    grid         = models.ForeignKey(Grid)
    title        = models.CharField(_('Title'), max_length=100)
    description  = models.TextField(_('Description'), blank=True)
    
    def save(self, *args, **kwargs):
        self.grid.grid_packages # fire the cache
        super(Feature, self).save(*args, **kwargs)
    
    def __unicode__(self):
        return '%s : %s' % (self.grid.slug, self.title)    
    
help_text = """
Linebreaks are turned into 'br' tags<br />
Urls are turned into links<br />
You can use just 'check', 'yes', 'good' to place a checkmark icon.<br />
You can use 'bad', 'negative', 'evil', 'sucks', 'no' to place a negative icon.<br />
Plus just '+' or '-' signs can be used but cap at 3 multiples to protect layout<br/>

"""
    
class Element(BaseModel):
    """ The individual cells on the grid.
    The ``Element`` grid attributes are:

    * :attr:`grid_package` - foreign key to :class:`~apps.grid.models.GridPackage`
    * :attr:`feature` - foreign key to :class:`~apps.grid.models.Feature`
    * :attr:`text` - the actual contents of the grid cell
    """
    
    grid_package = models.ForeignKey(GridPackage)
    feature      = models.ForeignKey(Feature)
    text         = models.TextField(_('text'), blank=True, help_text=help_text)
    
    class Meta:
        
        ordering = ["-id"]

    def save(self, *args, **kwargs):
        self.feature.save() # fire grid_packages cache
        super(Element, self).save(*args, **kwargs)
    
    def __unicode__(self):
        return '%s : %s : %s' % (self.grid_package.grid.slug, self.grid_package.package.slug, self.feature.title)
    
    
