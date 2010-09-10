from tastypie.resources import ModelResource

from apps.package.models import Package, Category, Repo

class PackageResource(ModelResource):
    
    class Meta:
        queryset = Package.objects.all()
        resource_name = 'package'
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