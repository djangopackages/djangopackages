from tastypie.resources import ModelResource

from grid.models import Grid

class GridResource(ModelResource):
    
    class Meta:
        queryset = Grid.objects.all()
        resource_name = 'grid'
        allowed_methods = ['get']
        include_absolute_url = True