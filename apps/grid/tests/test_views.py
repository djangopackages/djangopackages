from django.test import TestCase
from django.core.urlresolvers import reverse

from grid.models import Grid, Element, Feature, GridPackage
from package.models import Package

class FunctionalGridTest(TestCase):
    fixtures = ['test_initial_data.json']
    
    def test_grid_list_view(self):
        url = reverse('grids')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'grid/grids.html')
        
    def test_grid_detail_view(self):
        url = reverse('grid', kwargs={'slug': 'testing'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'grid/grid_detail.html')

    def test_grid_detail_feature_view(self):
        url = reverse('grid_detail_feature',
                      kwargs={'slug':'testing',
                              'feature_id':'1',
                              'bogus_slug':'508-compliant'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'grid/grid_detail_feature.html')

    def test_grid_detail_feature_view_contents(self):
        url = reverse('grid_detail_feature',
                      kwargs={'slug':'testing',
                              'feature_id':'1',
                              'bogus_slug':'508-compliant'})
        response = self.client.get(url)
        self.assertContains(response, '<a href="/">home</a>')
        self.assertContains(response, '<a href="/grids/">grids</a>')
        self.assertContains(response, '<a href="/grids/g/testing/">Testing</a>')
        self.assertContains(response, '<a href="/grids/testing/edit/">')
        self.assertContains(response, 'Has tests?')
        self.assertContains(response,
                            '<a href="/packages/p/testability/">Testability')
        self.assertContains(response,
                            '<a href="/packages/p/supertester/">Supertester')
        self.assertContains(response,
                            '<td class="clickable" id="element-f1-p1"><img')
        self.assertNotContains(response,
                            '<td class="clickable" id="element-f1-p2"><img')

    def test_add_grid_view(self):
        url = reverse('add_grid')
        response = self.client.get(url)
        
        # The response should be a redirect, since the user is not logged in.
        self.assertEqual(response.status_code, 302)
        
        # Once we log in the user, we should get back the appropriate response.
        self.assertTrue(self.client.login(username='user', password='user'))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'grid/add_grid.html')
    
        # Test form post
        count = Grid.objects.count()
        response = self.client.post(url, {
            'title': 'TEST TITLE',
            'slug': 'test-title',
            'description': 'Just a test description'
        }, follow=True)
        self.assertEqual(Grid.objects.count(), count + 1)
        self.assertContains(response, 'TEST TITLE')

    def test_edit_grid_view(self):
        url = reverse('edit_grid', kwargs={'slug': 'testing'})
        response = self.client.get(url)
        
        # The response should be a redirect, since the user is not logged in.
        self.assertEqual(response.status_code, 302)
        
        # Once we log in the user, we should get back the appropriate response.
        self.assertTrue(self.client.login(username='user', password='user'))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'grid/edit_grid.html')
    
        # Test form post
        count = Grid.objects.count()
        response = self.client.post(url, {
            'title': 'TEST TITLE',
            'slug': 'testing',
            'description': 'Just a test description'
        }, follow=True)
        self.assertEqual(Grid.objects.count(), count)
        self.assertContains(response, 'TEST TITLE')

    def test_add_feature_view(self):
        url = reverse('add_feature', kwargs={'grid_slug': 'testing'})
        response = self.client.get(url)
        
        # The response should be a redirect, since the user is not logged in.
        self.assertEqual(response.status_code, 302)
        
        # Once we log in the user, we should get back the appropriate response.
        self.assertTrue(self.client.login(username='user', password='user'))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'grid/add_feature.html')
        
        # Test form post
        count = Feature.objects.count()
        response = self.client.post(url, {
            'title': 'TEST TITLE',
            'description': 'Just a test description'
        }, follow=True)
        self.assertEqual(Feature.objects.count(), count + 1)
        self.assertContains(response, 'TEST TITLE')

    def test_edit_feature_view(self):
        url = reverse('edit_feature', kwargs={'id': '1'})
        response = self.client.get(url)
        
        # The response should be a redirect, since the user is not logged in.
        self.assertEqual(response.status_code, 302)
        
        # Once we log in the user, we should get back the appropriate response.
        self.assertTrue(self.client.login(username='user', password='user'))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'grid/edit_feature.html')

        # Test form post
        count = Feature.objects.count()
        response = self.client.post(url, {
            'title': 'TEST TITLE',
            'description': 'Just a test description'
        }, follow=True)
        self.assertEqual(Feature.objects.count(), count)
        self.assertContains(response, 'TEST TITLE')

    def test_delete_feature_view(self):
        count = Feature.objects.count()
        
        # Since this user doesn't have the appropriate permissions, none of the
        # features should be deleted (thus the count should be the same).
        self.assertTrue(self.client.login(username='user', password='user'))
        url = reverse('delete_feature', kwargs={'id': '1'})
        response = self.client.get(url)
        self.assertEqual(count, Feature.objects.count())
        
        # Once we log in with the appropriate user, the request should delete
        # the given feature, reducing the count by one.
        self.assertTrue(self.client.login(username='cleaner', password='cleaner'))
        response = self.client.get(url)
        self.assertEqual(Feature.objects.count(), count - 1)

    def test_edit_element_view(self):
        url = reverse('edit_element', kwargs={'feature_id': '1', 'package_id': '1'})
        response = self.client.get(url)
        
        # The response should be a redirect, since the user is not logged in.
        self.assertEqual(response.status_code, 302)
        
        # Once we log in the user, we should get back the appropriate response.
        self.assertTrue(self.client.login(username='user', password='user'))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'grid/edit_element.html')

        # Test form post
        count = Element.objects.count()
        response = self.client.post(url, {
            'text': 'Some random text',
        }, follow=True)
        self.assertEqual(Element.objects.count(), count)
        self.assertContains(response, 'Some random text')

        # Confirm 404 if grid IDs differ
        url = reverse('edit_element', kwargs={'feature_id': '1', 'package_id': '4'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)


    def test_add_grid_package_view(self):
        url = reverse('add_grid_package', kwargs={'grid_slug': 'testing'})
        response = self.client.get(url)
        
        # The response should be a redirect, since the user is not logged in.
        self.assertEqual(response.status_code, 302)
        
        # Once we log in the user, we should get back the appropriate response.
        self.assertTrue(self.client.login(username='user', password='user'))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'grid/add_grid_package.html')

        # Test form post for existing grid package
        response = self.client.post(url, {
            'package': 2,
        })
        self.assertContains(response, 
                            '&#39;Supertester&#39; is already in this grid.')
        # Test form post for new grid package
        count = GridPackage.objects.count()
        response = self.client.post(url, {
            'package': 4,
        }, follow=True)
        self.assertEqual(GridPackage.objects.count(), count + 1)
        self.assertContains(response, 'Another Test')


    def test_add_new_grid_package_view(self):
        url = reverse('add_new_grid_package', kwargs={'grid_slug': 'testing'})
        response = self.client.get(url)

        # The response should be a redirect, since the user is not logged in.
        self.assertEqual(response.status_code, 302)
        
        # Once we log in the user, we should get back the appropriate response.
        self.assertTrue(self.client.login(username='user', password='user'))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'package/package_form.html')

        # Test form post
        count = Package.objects.count()
        response = self.client.post(url, {
            'repo_url': 'http://www.example.com',
            'title': 'Test package',
            'slug': 'test-package',
            'pypi_url': 'http://pypi.python.org/pypi/mogo/0.1.1',
            'category': 1 
        }, follow=True)
        self.assertEqual(Package.objects.count(), count + 1)
        self.assertContains(response, 'Test package')


    def test_ajax_grid_list_view(self):
        url = reverse('ajax_grid_list') + '?q=Testing&package_id=4' 
        response = self.client.get(url)
        self.assertContains(response, 'Testing')


    def test_delete_gridpackage_view(self):
        count = GridPackage.objects.count()
        
        # Since this user doesn't have the appropriate permissions, none of the
        # features should be deleted (thus the count should be the same).
        self.assertTrue(self.client.login(username='user', password='user'))
        url = reverse('delete_grid_package', kwargs={'id': '1'})
        response = self.client.get(url)
        self.assertEqual(count, GridPackage.objects.count())
        
        # Once we log in with the appropriate user, the request should delete
        # the given feature, reducing the count by one.
        self.assertTrue(self.client.login(username='cleaner', password='cleaner'))
        response = self.client.get(url)
        self.assertEqual(count - 1, GridPackage.objects.count())

    def test_latest_grids_view(self):
        url = reverse('latest_grids')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'grid/grid_archive.html')

class RegressionGridTest(TestCase):
    fixtures = ['test_initial_data.json']
    
    def test_edit_element_view_for_nonexistent_elements(self):
        """Make sure that attempts to edit nonexistent elements succeed.
        
        """
        # Delete the element for the sepcified feature and package.        
        element, created = Element.objects.get_or_create(feature=1, grid_package=1)
        element.delete()
        
        # Log in the test user and attempt to edit the element.
        self.assertTrue(self.client.login(username='user', password='user'))

        url = reverse('edit_element', kwargs={'feature_id': '1', 'package_id': '1'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'grid/edit_element.html')
            
