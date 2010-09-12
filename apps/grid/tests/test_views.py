from django.test import TestCase
from django.test.client import Client
from django.core.urlresolvers import reverse

from grid.models import Element

class FunctionalGridTest(TestCase):
    fixtures = ['test_initial_data.json']
    
    def test_grid_list_view(self):
        c = Client()
        url = reverse('grids')
        response = c.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'grid/grids.html')
        
    def test_grid_detail_view(self):
        c = Client()
        url = reverse('grid', kwargs={'slug': 'testing'})
        response = c.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'grid/grid_detail.html')
    
    def test_add_grid_view(self):
        c = Client()
        url = reverse('add_grid')
        response = c.get(url)
        
        # The response should be a redirect, since the user is not logged in.
        self.assertEqual(response.status_code, 302)
        
        # Once we log in the user, we should get back the appropriate response.
        self.assertTrue(c.login(username='user', password='user'))
        response = c.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'grid/add_grid.html')
    
    def test_edit_grid_view(self):
        c = Client()
        url = reverse('edit_grid', kwargs={'slug': 'testing'})
        response = c.get(url)
        
        # The response should be a redirect, since the user is not logged in.
        self.assertEqual(response.status_code, 302)
        
        # Once we log in the user, we should get back the appropriate response.
        self.assertTrue(c.login(username='user', password='user'))
        response = c.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'grid/edit_grid.html')
    
    def test_add_feature_view(self):
        c = Client()
        url = reverse('add_feature', kwargs={'grid_slug': 'testing'})
        response = c.get(url)
        
        # The response should be a redirect, since the user is not logged in.
        self.assertEqual(response.status_code, 302)
        
        # Once we log in the user, we should get back the appropriate response.
        self.assertTrue(c.login(username='user', password='user'))
        response = c.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'grid/add_feature.html')
        
    def test_edit_feature_view(self):
        c = Client()
        url = reverse('edit_feature', kwargs={'id': '1'})
        response = c.get(url)
        
        # The response should be a redirect, since the user is not logged in.
        self.assertEqual(response.status_code, 302)
        
        # Once we log in the user, we should get back the appropriate response.
        self.assertTrue(c.login(username='user', password='user'))
        response = c.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'grid/edit_feature.html')

    def test_edit_element_view(self):
        c = Client()
        url = reverse('edit_element', kwargs={'feature_id': '1', 'package_id': '1'})
        response = c.get(url)
        
        # The response should be a redirect, since the user is not logged in.
        self.assertEqual(response.status_code, 302)
        
        # Once we log in the user, we should get back the appropriate response.
        self.assertTrue(c.login(username='user', password='user'))
        response = c.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'grid/edit_element.html')

    def test_add_gridpackage_view(self):
        c = Client()
        url = reverse('add_grid_package', kwargs={'grid_slug': 'testing'})
        response = c.get(url)
        
        # The response should be a redirect, since the user is not logged in.
        self.assertEqual(response.status_code, 302)
        
        # Once we log in the user, we should get back the appropriate response.
        self.assertTrue(c.login(username='user', password='user'))
        response = c.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'grid/add_grid_package.html')

    def test_latest_grids_view(self):
        c = Client()
        url = reverse('latest_grids')
        response = c.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'grid/grid_archive.html')

class RegressionGridTest(TestCase):
    fixtures = ['test_initial_data.json']
    
    def test_edit_element_view_for_nonexistent_elements(self):
        """Make sure that attempts to edit nonexistent elements succeed.
        
        """
        c = Client()

        # Delete the element for the sepcified feature and package.        
        element, created = Element.objects.get_or_create(feature=1, grid_package=1)
        element.delete()
        
        # Log in the test user and attempt to edit the element.
        self.assertTrue(c.login(username='user', password='user'))

        url = reverse('edit_element', kwargs={'feature_id': '1', 'package_id': '1'})
        response = c.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'grid/edit_element.html')
            












        