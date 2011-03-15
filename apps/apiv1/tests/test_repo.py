import json
from django.test import TestCase
from django.core.urlresolvers import reverse
import os

this_directory = os.path.dirname(__file__)
apps_directory = os.path.join(this_directory, '..', '..')
fixtures_directory = os.path.join(apps_directory, 'grid', 'fixtures')
fixture_path = os.path.join(fixtures_directory, 'test_initial_data.json')

class RepoTests(TestCase):
    fixtures = [fixture_path]
    base_kwargs = {'api_name': 'v1'}
    
        
    def test_repo(self):
        # Fetch the response        
        kwargs = {'resource_name': 'repo'}
        kwargs.update(self.base_kwargs)
        url = reverse('api_dispatch_list', kwargs=kwargs)
        response = self.client.get(url)
        
        # check 200
        self.assertEqual(response.status_code, 200)
        
        # confirm data points
        data = json.loads(response.content)
        
        self.assertEquals(data["meta"]["limit"], 20)
        self.assertEquals(data["meta"]["limit"], 20)
        self.assertEquals(data["objects"][0]["is_supported"], True)