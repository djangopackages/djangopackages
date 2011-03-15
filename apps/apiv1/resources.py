from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from tastypie import fields
from tastypie.bundle import Bundle
from tastypie.exceptions import NotFound
from tastypie.resources import ModelResource

from django.conf.urls.defaults import url
from grid.models import Grid
from homepage.models import Dpotw, Gotw
from package.models import Package, Category
from tastypie import fields
from tastypie.resources import ModelResource


# TODO - exclude ID, repo_commits, and other fields not yet used

class BaseResource(ModelResource):
    
    def determine_format(self, *args, **kwargs):
        
        return "application/json"

class EnhancedModelResource(BaseResource):
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
        excludes = ["id"]
        
    def override_urls(self):
        return [
            url(
                r"^%s/(?P<grid_name>[-\w]+)/packages/$" % GridResource._meta.resource_name,
                self.get_packages,
            ),
        ] 

    def get_packages(self, request, **kwargs):
        """
        Returns a serialized list of resources based on the identifiers
        from the URL.
        
        Calls ``obj_get`` to fetch only the objects requested. This method
        only responds to HTTP GET.
        
        Should return a HttpResponse (200 OK).
        """
        self.method_check(request, allowed=['get'])
        self.is_authenticated(request)
        self.throttle_check(request)
        
        qs = Package.objects.filter(grid__slug=kwargs['grid_name'])
        pkg = PackageResource()
        object_list = [pkg.full_dehydrate(obj) for obj in qs]
        
        self.log_throttled_access(request)
        return self.create_response(request, object_list)


class DpotwResource(ModelResource):

    class Meta:
        queryset = Dpotw.objects.all()
        resource_name = 'package-of-the-week'
        allowed_methods = ['get']
        include_absolute_url = True
        lookup_field = 'package__slug'
        excludes = ["id"]        

class GotwResource(EnhancedModelResource):

    class Meta:
        queryset = Gotw.objects.all()
        resource_name = 'grid-of-the-week'
        allowed_methods = ['get']
        include_absolute_url = True
        lookup_field = 'grid__slug'
        excludes = ["id"]        
        

class CategoryResource(EnhancedModelResource):

    class Meta:
        queryset = Category.objects.all()
        resource_name = 'category'
        allowed_methods = ['get']
        lookup_field = 'slug'
        excludes = ["id"]        

class UserResource(EnhancedModelResource):

    class Meta:
        queryset = User.objects.all().order_by("-id")
        resource_name = 'user'
        allowed_methods = ['get']
        lookup_field = 'username'        
        fields = ["resource_uri", "last_login", "username", "date_joined"]
        

class PackageResource(PackageResourceBase):

    category    = fields.ForeignKey(CategoryResource, "category")
    grids       = fields.ToManyField(GridResource, "grid_set")
    created_by  = fields.ForeignKey(UserResource, "created_by", null=True)
    last_modified_by  = fields.ForeignKey(UserResource, "created_by", null=True)
    pypi_version = fields.CharField('pypi_version')
    commits_over_52 = fields.CharField('commits_over_52')

    class Meta:
        queryset = Package.objects.all()
        resource_name = 'package'
        allowed_methods = ['get']
        include_absolute_url = True
        lookup_field = 'slug'
        
