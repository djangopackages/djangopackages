from datetime import datetime, timedelta

from django.urls import reverse
from django.test import TestCase

from grid.models import Grid
from homepage.models import Dpotw, Gotw
from package.models import Package, Category

from homepage.tests import data


class FunctionalHomepageTest(TestCase):
    def setUp(self):
        data.load()

    def test_homepage_view(self):
        url = reverse('home')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'homepage.html')

        for p in Package.objects.all():
            self.assertContains(response, p.title)
            self.assertContains(response, p.repo_description)

        self.assertEqual(response.context['package_count'], Package.objects.count())

    def test_categories_on_homepage(self):
        url = reverse('home')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'homepage.html')

        for c in Category.objects.all():
            self.assertContains(response, c.title_plural)
            self.assertContains(response, c.description)


class FunctionalHomepageTestWithoutPackages(TestCase):
    def setUp(self):
        data.load()

    def test_homepage_view(self):
        Package.objects.all().delete()
        url = reverse('home')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'homepage.html')


class TestErrorPages(TestCase):

    def test_404_test(self):
        r = self.client.get("/404")
        self.assertEqual(r.status_code, 404)

    def test_500_test(self):
        r = self.client.get("/500")
        self.assertEqual(r.status_code, 500)
