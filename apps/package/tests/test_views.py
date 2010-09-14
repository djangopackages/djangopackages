from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.client import Client

class FunctionalPackageTest(TestCase):
    fixtures = ['test_initial_data.json']
    
    def test_package_list_view(self):
        url = reverse('packages')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'package/package_list.html')
        
    def test_package_detail_view(self):
        url = reverse('package', kwargs={'slug': 'testability'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'package/package.html')
    
    def test_latest_packages_view(self):
        url = reverse('latest_packages')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'package/package_archive.html')
    
    def test_add_package_view(self):
        url = reverse('add_package')
        response = self.client.get(url)
        
        # The response should be a redirect, since the user is not logged in.
        self.assertEqual(response.status_code, 302)
        
        # Once we log in the user, we should get back the appropriate response.
        self.assertTrue(self.client.login(username='user', password='user'))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'package/package_form.html')
    
    def test_edit_package_view(self):
        url = reverse('edit_package', kwargs={'slug': 'testability'})
        response = self.client.get(url)
        
        # The response should be a redirect, since the user is not logged in.
        self.assertEqual(response.status_code, 302)
        
        # Once we log in the user, we should get back the appropriate response.
        self.assertTrue(self.client.login(username='user', password='user'))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'package/package_form.html')
    
    def test_add_example_view(self):
        url = reverse('add_example', kwargs={'slug': 'testability'})
        response = self.client.get(url)
        
        # The response should be a redirect, since the user is not logged in.
        self.assertEqual(response.status_code, 302)
        
        # Once we log in the user, we should get back the appropriate response.
        self.assertTrue(self.client.login(username='user', password='user'))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'package/add_example.html')
        
    def test_edit_example_view(self):
        url = reverse('edit_example', kwargs={'slug': 'testability', 'id': '1'})
        response = self.client.get(url)
        
        # The response should be a redirect, since the user is not logged in.
        self.assertEqual(response.status_code, 302)
        
        # Once we log in the user, we should get back the appropriate response.
        self.assertTrue(self.client.login(username='user', password='user'))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'package/edit_example.html')

    def test_usage_view(self):
        url = reverse('usage', kwargs={'slug': 'testability', 'action': 'add'})
        response = self.client.get(url)

        # The response should be a redirect, since the user is not logged in.
        self.assertEqual(response.status_code, 302)
        
        user = User.objects.get(username='user')
        count = user.package_set.count()
        self.assertTrue(self.client.login(username='user', password='user'))
        

        # Now that the user is logged in, make sure that the number of packages
        # they use has increased by one.
        response = self.client.get(url)
        self.assertEqual(count + 1, user.package_set.count())
        
        # Now we remove that same package from the user's list of used packages,
        # making sure that the total number has decreased by one.
        url = reverse('usage', kwargs={'slug': 'testability', 'action': 'remove'})
        response = self.client.get(url)
        self.assertEqual(count, user.package_set.count())

class RegressionPackageTest(TestCase):
    pass
