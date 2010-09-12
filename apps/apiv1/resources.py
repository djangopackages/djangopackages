from tastypie import fields
from tastypie.exceptions import NotFound
from tastypie.resources import ModelResource
from tastypie.bundle import Bundle
from django.core.urlresolvers import reverse

from grid.models import Grid
from homepage.models import Dpotw, Gotw
from package.models import Package, Category, Repo

class EnhancedModelResource(ModelResource):
    def obj_get(self, **kwargs):
        """
        A ORM-specific implementation of ``obj_get``.
        
        Takes optional ``kwargs``, which are used to narrow the query to find
        the instance.
        """
        lookup_field = getattr(self._meta, 'lookup_field', 'pk')
        try:
            return self._meta.queryset.get(**{lookup_field: kwargs['pk']})
        except ValueError, e:
            raise NotFound("Invalid resource lookup data provided (mismatched type).")
        
    def get_resource_value(self, obj):
        lookup_field = getattr(self._meta, 'lookup_field', 'pk')
        lookups = lookup_field.split('__')
        for lookup in lookups:
            obj = getattr(obj, lookup)
        return obj

    def get_resource_uri(self, bundle_or_obj):
        """
        Handles generating a resource URI for a single resource.
        
        Uses the model's ``pk`` in order to create the URI.
        """
        kwargs = {
            'resource_name': self._meta.resource_name,
        }
        
        if isinstance(bundle_or_obj, Bundle):
            kwargs['pk'] = self.get_resource_value(bundle_or_obj.obj)
        else:
            kwargs['pk'] = self.get_resource_value(bundle_or_obj)
        
        if self._meta.api_name is not None:
            kwargs['api_name'] = self._meta.api_name
        
        return reverse("api_dispatch_detail", kwargs=kwargs)


class PackageResourceBase(EnhancedModelResource):    

    class Meta:
        queryset = Package.objects.all()
        resource_name = 'package'
        allowed_methods = ['get']
        include_absolute_url = True
        lookup_field = 'slug'


class GridResource(EnhancedModelResource):
    
    packages = fields.ToManyField(PackageResourceBase, "packages")    
    
    class Meta:
        queryset = Grid.objects.all()
        resource_name = 'grid'
        allowed_methods = ['get']
        include_absolute_url = True
        lookup_field = 'slug'

class DpotwResource(EnhancedModelResource):

    class Meta:
        queryset = Dpotw.objects.all()
        resource_name = 'package-of-the-week'
        allowed_methods = ['get']
        include_absolute_url = True
        lookup_field = 'package__slug'

class GotwResource(EnhancedModelResource):

    class Meta:
        queryset = Gotw.objects.all()
        resource_name = 'grid-of-the-week'
        allowed_methods = ['get']
        include_absolute_url = True
        lookup_field = 'grid__slug'
        

class CategoryResource(EnhancedModelResource):

    class Meta:
        queryset = Category.objects.all()
        resource_name = 'category'
        allowed_methods = ['get']
        lookup_field = 'slug'

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
        lookup_field = 'slug'