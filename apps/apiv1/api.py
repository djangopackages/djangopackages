from django.core.urlresolvers import reverse
from django.http import HttpResponse

from tastypie.api import Api as TastyPieApi
from tastypie.serializers import Serializer
from tastypie.utils.mime import build_content_type

class Api(TastyPieApi):

    def top_level(self, request, api_name=None):
        """
        A view that returns a serialized list of all resources registers
        to the ``Api``. Useful for discovery.
        """
        serializer = Serializer()
        available_resources = {}
    
        if api_name is None:
            api_name = self.api_name
    
        for name in sorted(self._registry.keys()):
            available_resources[name] = reverse("api_dispatch_list", kwargs={
                'api_name': api_name,
                'resource_name': name,
            })
    
        desired_format = "application/json"
        serialized = serializer.serialize(available_resources, desired_format)
        return HttpResponse(content=serialized, content_type=build_content_type(desired_format))
