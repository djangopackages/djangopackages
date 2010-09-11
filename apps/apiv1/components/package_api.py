from tastypie import fields
from tastypie.resources import ModelResource

from package.models import Package, Category, Repo
        
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
        
class PackageResource(ModelResource):
    
    category = fields.ForeignKey(CategoryResource, "category")
    repo = fields.ForeignKey(RepoResource, "repo")    

    class Meta:
        queryset = Package.objects.all()
        resource_name = 'package'
        allowed_methods = ['get']
        include_absolute_url = True
        