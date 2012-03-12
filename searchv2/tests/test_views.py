from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase

from package.models import Package
from package.tests import initial_data
from profiles.models import Profile
from searchv2.builders import build_1
from searchv2.models import SearchV2
from searchv2.views import search_function


class FunctionalPackageTest(TestCase):
    def setUp(self):
        initial_data.load()
        for user in User.objects.all():
            profile = Profile.objects.create(user=user)
            profile.save()

    def test_build_search(self):

        count = SearchV2.objects.count()
        url = reverse('build_search')
        response = self.client.get(url)
        self.assertEquals(response.status_code, 302)
        self.assertEquals(count, 0)        
        
        self.assertTrue(self.client.login(username='user', password='user'))
        response = self.client.get(url)
        self.assertEquals(response.status_code, 403)
        self.assertEquals(count, 0)        

        self.assertTrue(self.client.login(username='admin', password='admin'))
        response = self.client.get(url)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(count, 0)        

        response = self.client.post(url)
        self.assertEquals(response.status_code, 200)
        self.assertEquals(SearchV2.objects.count(), 6)
        
    def test_search_function(self):
        build_1(False)
        results = search_function('ser')
        self.assertEquals(results[0].title, 'Serious Testing')
