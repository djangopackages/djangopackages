import json

from django.core.urlresolvers import reverse
from django.test import TestCase


class RepoTests(TestCase):
    fixtures = ['test_initial_data.json']
    base_kwargs = {'api_name': 'v1'}
    
    def grab_response(self):
        # Fetch the response        
        kwargs = {'resource_name': 'repo'}
        kwargs.update(self.base_kwargs)
        url = reverse('api_dispatch_list', kwargs=kwargs)
        response = self.client.get(url)
        
        # check 200
        self.assertEqual(response.status_code, 200)
        
        # confirm data points
        return json.loads(response.content)        
    
        
    def test_repo_object_attributes(self):
        # confirm data points
        data = self.grab_response()
        
        objects = data["objects"][0]
        
        self.assertEquals(objects['is_supported'], True)
