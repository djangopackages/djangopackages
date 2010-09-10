from tastypie.resources import ModelResource

from homepage.models import Dpotw, Gotw

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