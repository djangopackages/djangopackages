from django.test import TestCase
from django.core.urlresolvers import reverse
from apiv1.tests import data


class ResourcesV1Tests(TestCase):
    base_kwargs = {'api_name': 'v1'}

    def setUp(self):
        data.load()

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

        query_filter = "?category__slug=apps"
        cat_filter_url = "%s%s" % (list_url, query_filter)
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

    def test_03_package(self):
        kwargs = {'resource_name': 'package'}
        kwargs.update(self.base_kwargs)
        # check 200's
        list_url = reverse('api_dispatch_list', kwargs=kwargs)
        response = self.client.get(list_url)
        self.assertEqual(response.status_code, 200)

        kwargs['pk'] = 'testability'
        package_url = reverse('api_dispatch_detail', kwargs=kwargs)
        self.assertTrue(package_url in response.content)
        response = self.client.get(package_url)
        self.assertEqual(response.status_code, 200)
