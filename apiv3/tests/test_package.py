from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase
from grid.models import Grid, GridPackage
from package.models import Package, Category
import json
from requests.compat import urlencode




class PackageV1Tests(TestCase):
    def setUp(self):
        """
        Set up initial data, done through Python because fixtures break way too
        quickly with migrations and are terribly hard to maintain.
        """
        self.app = Category.objects.create(
            title='App',
            slug='app',
        )
        self.framework = Category.objects.create(
            title='Framework',
            slug='framework',
        )
        self.grid = Grid.objects.create(
            title='A Grid',
            slug='grid',
        )
        self.pkg1 = Package.objects.create(
            title='Package1',
            slug='package1',
            category=self.app,
            repo_url='https://github.com/pydanny/django-uni-form'
        )
        self.pkg2 = Package.objects.create(
            title='Package2',
            slug='package2',
            category=self.app,
            repo_url='https://github.com/cartwheelweb/opencomparison'  
        )
        self.pkg3 = Package.objects.create(
            title='Package3',
            slug='package3',
            category=self.framework,
            repo_url='https://github.com/divio/django-cms'
        )
        GridPackage.objects.create(package=self.pkg1, grid=self.grid)
        GridPackage.objects.create(package=self.pkg2, grid=self.grid)
        user = User.objects.create_user('user', 'user@opencomparison.com', 'user')
        self.pkg1.usage.add(user)

    def test_01_packages_usage(self):
        urlkwargs_pkg1 = {
            'api_name': 'v1',
            'resource_name': 'package',
            'pk': self.pkg1.slug,
        }
        url_pkg1 = reverse('api_dispatch_detail', kwargs=urlkwargs_pkg1)
        response_pkg1 = self.client.get(url_pkg1)
        # check that the request was successful
        self.assertEqual(response_pkg1.status_code, 200)
        # check that we have a usage_count equal to the one in the DB
        raw_json_pkg1 = response_pkg1.content
        pkg_1 = json.loads(raw_json_pkg1)
        usage_count_pkg1 = int(pkg_1['usage_count'])
        self.assertEqual(usage_count_pkg1, self.pkg1.usage.count())
        # do the same with pkg2
        urlkwargs_pkg2 = {
            'api_name': 'v1',
            'resource_name': 'package',
            'pk': self.pkg2.slug,
        }
        url_pkg2 = reverse('api_dispatch_detail', kwargs=urlkwargs_pkg2)
        response_pkg2 = self.client.get(url_pkg2)
        # check that the request was successful
        self.assertEqual(response_pkg2.status_code, 200)
        # check that we have a usage_count equal to the one in the DB
        raw_json_pkg2 = response_pkg2.content
        pkg_2 = json.loads(raw_json_pkg2)
        usage_count_pkg2 = int(pkg_2['usage_count'])
        self.assertEqual(usage_count_pkg2, self.pkg2.usage.count())

    def test_02_category_packages(self):
        urlkwargs_pkg_list = {
            'api_name': 'v1',
            'resource_name': 'package',
        }
        querystring_filter_app = {
            'category__slug': self.app.slug
        }
        url_app_pkg = "%s?%s" % (reverse('api_dispatch_list',
            kwargs=urlkwargs_pkg_list), urlencode(querystring_filter_app))
        response_app_pkg = self.client.get(url_app_pkg)
        # check that the request was successful
        self.assertEqual(response_app_pkg.status_code, 200)
        # check that we have correct number of packages in filter
        raw_json_app_pkg = response_app_pkg.content
        app_pkg = json.loads(raw_json_app_pkg)
        app_pkg_count = int(app_pkg['meta']['total_count'])
        self.assertEqual(app_pkg_count, self.app.package_set.count())
        # Check that we have filter applied correclty
        app_package_slug_list = self.app.package_set.values_list('slug', flat=True)
        self.assertIn(self.pkg1.slug, app_package_slug_list)
        self.assertIn(self.pkg2.slug, app_package_slug_list)
