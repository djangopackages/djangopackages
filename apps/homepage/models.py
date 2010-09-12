import datetime

from django.db import models
from django.utils.translation import ugettext_lazy as _ 

from grid.models import Grid
from package.models import BaseModel, Package

class RotatorManager(models.Manager):
    
    def get_current(self):
        now = datetime.datetime.now()
        return self.get_query_set().filter(start_date__lte=now, end_date__gte=now)

class Dpotw(BaseModel):
    
    package = models.ForeignKey(Package)
    start_date = models.DateField(_("Start Date"))
    end_date = models.DateField(_("End Date"))    
    
    objects = RotatorManager()
    
    class Meta:
        ordering = ('-start_date', '-end_date',)
        
        verbose_name         = "Django Package of the Week"
        verbose_name_plural  = "Django Packages of the Week"
        
    def __unicode__(self):
        return '%s : %s - %s' % (self.package.title, self.start_date, self.end_date)
        
    @models.permalink
    def get_absolute_url(self):
        return ("package", [self.package.slug])        

class Gotw(BaseModel):
    
    grid = models.ForeignKey(Grid)
    
    start_date = models.DateField(_("Start Date"))
    end_date = models.DateField(_("End Date"))
    
    objects = RotatorManager()
    
    class Meta:
        ordering = ('-start_date', '-end_date',)        
        
        verbose_name         = "Grid of the Week"
        verbose_name_plural  = "Grids of the Week"
    
    def __unicode__(self):
        return '%s : %s - %s' % (self.grid.title, self.start_date, self.end_date)
        
    @models.permalink
    def get_absolute_url(self):
        return ("grid", [self.grid.slug])        
        
class Tab(BaseModel):
    
    grid = models.ForeignKey(Grid)
    order = models.IntegerField(_("Order displayed on the home page"), default="0")

    class Meta:
        
        ordering = ['order', 'grid']
        verbose_name         = "Tab"
        verbose_name_plural  = "Tabs"
    
    def __unicode__(self):
        return self.grid.title
    