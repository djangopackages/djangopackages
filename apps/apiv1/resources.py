from tastypie import fields
from tastypie.resources import ModelResource

from grid.models import Grid
from homepage.models import Dpotw, Gotw
from package.models import Package, Category, Repo

class PackageResourceBase(ModelResource):    

    class Meta:
        queryset = Package.objects.all()
        resource_name = 'package'
        allowed_methods = ['get']
        include_absolute_url = True


class GridResource(ModelResource):    
    
    packages = fields.ToManyField(PackageResourceBase, "packages")    
    
    class Meta:
        queryset = Grid.objects.all()
        resource_name = 'grid'
        allowed_methods = ['get']
        include_absolute_url = True

class DpotwResource(ModelResource):

    class Meta:
        queryset = Dpotw.objects.all()
        resource_name = 'package-of-the-week'
        allowed_methods = ['get']
        include_absolute_url = True

class GotwResource(ModelResource):

    class Meta:
        queryset = Gotw.objects.all()
        resource_name = 'grid-of-the-week'
        allowed_methods = ['get']
        include_absolute_url = True     
        

class CategoryResource(ModelResource):

    class Meta:
        queryset = Category.objects.all()
        resource_name = 'category'
        allowed_methods = ['get']        

class RepoResource(ModelResource):

    class Meta:
        queryset = Repo.objects.all()
        resource_name = 'repo'
        allowed_methods = ['get']

class PackageResource(PackageResourceBase):

    category    = fields.ForeignKey(CategoryResource, "category")
    repo        = fields.ForeignKey(RepoResource, "repo")    
    grids       = fields.ToManyField(GridResource, "grid_set")

    class Meta:
        queryset = Package.objects.all()
        resource_name = 'package'
        allowed_methods = ['get']
        include_absolute_url = True           