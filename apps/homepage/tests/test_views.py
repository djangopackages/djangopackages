from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.client import Client

class FunctionalHomepageTest(TestCase):
    fixtures = ['test_initial_data.json']
    
    def test_homepage_view(self):
        url = reverse('home')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'homepage.html')

class RegressionHomepageTest(TestCase):
    pass
