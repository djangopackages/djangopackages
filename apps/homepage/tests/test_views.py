from datetime import datetime, timedelta

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase

from grid.models import Grid
from homepage.models import Dpotw, Gotw
from package.models import Package, Category


class FunctionalHomepageTest(TestCase):
    fixtures = ['test_initial_data.json']

    def test_homepage_view(self):
        url = reverse('home')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'homepage.html')

        for p in Package.objects.all():
            self.assertContains(response, p.title)
            self.assertContains(response, p.repo_description)

        self.assertEquals(response.context['package_count'], Package.objects.count())

    def test_categories_on_homepage(self):
        url = reverse('home')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'homepage.html')

        for c in Category.objects.all():
            self.assertContains(response, c.title_plural)
            self.assertContains(response, c.description)

    def test_items_of_the_week(self):
        url = reverse('home')
        today = datetime.now()
        two_days_ago = today - timedelta(days=2)
        yesterday = today - timedelta(days=1)
        tomorrow = today + timedelta(days=1)

        p = Package.objects.all()[0]
        g = Grid.objects.all()[0]

        d_live = Dpotw.objects.create(package=p, start_date=yesterday, end_date=tomorrow)
        d_not_live = Dpotw.objects.create(package=p, start_date=two_days_ago, end_date=yesterday)

        g_live = Gotw.objects.create(grid=g, start_date=yesterday, end_date=tomorrow)
        g_not_live = Gotw.objects.create(grid=g, start_date=two_days_ago, end_date=yesterday)

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'homepage.html')
        self.assert_(d_live in response.context['dpotw'])
        self.assert_(d_not_live not in response.context['dpotw'])
        self.assert_(g_live in response.context['gotw'])
        self.assert_(g_not_live not in response.context['gotw'])