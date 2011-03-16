import json
from django.test import TestCase
from django.core.urlresolvers import reverse


class ResourcesV1Tests(TestCase):
    fixtures = ['test_initial_data.json']
    base_kwargs = {'api_name': 'v1'}
    
    def test_01_category(self):
        kwargs = {'resource_name': 'category'}
        kwargs.update(self.base_kwargs)
        # check 200's
        list_url = reverse('api_dispatch_list', kwargs=kwargs)
        response = self.client.get(list_url)
        self.assertEqual(response.status_code, 200)
        kwargs['pk'] = 'apps'
        cat_url = reverse('api_dispatch_detail', kwargs=kwargs)
        self.assertTrue(cat_url in response.content)
        response = self.client.get(cat_url)
        self.assertEqual(response.status_code, 200)
        
    def test_02_grid(self):
        kwargs = {'resource_name': 'grid'}
        kwargs.update(self.base_kwargs)
        # check 200's
        list_url = reverse('api_dispatch_list', kwargs=kwargs)
        response = self.client.get(list_url)
        self.assertEqual(response.status_code, 200)
        kwargs['pk'] = 'testing'
        grid_url = reverse('api_dispatch_detail', kwargs=kwargs)
        self.assertTrue(grid_url in response.content)
        response = self.client.get(grid_url)
        self.assertEqual(response.status_code, 200)
