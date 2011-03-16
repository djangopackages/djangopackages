from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase

from package.models import Category, Package, PackageExample


class FunctionalPackageTest(TestCase):
    fixtures = ['test_initial_data.json']

    def test_package_list_view(self):
        url = reverse('packages')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'package/package_list.html')
        packages = Package.objects.all()
        for p in packages:
            self.assertContains(response, p.title)

    def test_package_detail_view(self):
        url = reverse('package', kwargs={'slug': 'testability'})
        response = self.client.get(url)
        self.assertTemplateUsed(response, 'package/package.html')
        p = Package.objects.get(slug='testability')
        self.assertContains(response, p.title)
        self.assertContains(response, p.repo_description)
        for participant in p.participant_list():
            self.assertContains(response, participant)
        for g in p.grids():
            self.assertContains(response, g.title)
        for e in p.active_examples():
            self.assertContains(response, e.title)

    def test_latest_packages_view(self):
        url = reverse('latest_packages')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'package/package_archive.html')
        packages = Package.objects.all()
        for p in packages:
            self.assertContains(response, p.title)
            self.assertContains(response, p.repo_description)

    def test_add_package_view(self):
        url = reverse('add_package')
        response = self.client.get(url)

        # The response should be a redirect, since the user is not logged in.
        self.assertRedirects(response, '%s?next=%s' % (settings.LOGIN_URL, url))

        # Once we log in the user, we should get back the appropriate response.
        self.assertTrue(self.client.login(username='user', password='user'))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'package/package_form.html')
        for c in Category.objects.all():
            self.assertContains(response, c.title)
        count = Package.objects.count()
        response = self.client.post(url, {
            'category': Category.objects.all()[0].pk,
            'repo_url': 'http://github.com/django/django',
            'slug': 'test-slug',
            'title': 'TEST TITLE',
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Package.objects.count(), count + 1)

    def test_edit_package_view(self):
        p = Package.objects.get(slug='testability')
        url = reverse('edit_package', kwargs={'slug': 'testability'})
        response = self.client.get(url)

        # The response should be a redirect, since the user is not logged in.
        self.assertRedirects(response, '%s?next=%s' % (settings.LOGIN_URL, url))

        # Once we log in the user, we should get back the appropriate response.
        self.assertTrue(self.client.login(username='user', password='user'))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'package/package_form.html')
        self.assertContains(response, p.title)
        self.assertContains(response, p.slug)

        # Make a test post
        response = self.client.post(url, {
            'category': Category.objects.all()[0].pk,
            'repo_url': 'http://github.com/django/django',
            'slug': p.slug,
            'title': 'TEST TITLE',
        })
        self.assertEqual(response.status_code, 302)

        # Check that it actually changed the package
        p = Package.objects.get(slug='testability')
        self.assertEqual(p.title, 'TEST TITLE')

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

        count = PackageExample.objects.count()
        response = self.client.post(url, {
            'title': 'TEST TITLE',
            'url': 'http://github.com',
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(PackageExample.objects.count(), count + 1)

    def test_edit_example_view(self):
        e = PackageExample.objects.all()[0]
        id = e.pk
        url = reverse('edit_example', kwargs={'slug': e.package.slug,
            'id': e.pk})
        response = self.client.get(url)

        # The response should be a redirect, since the user is not logged in.
        self.assertEqual(response.status_code, 302)

        # Once we log in the user, we should get back the appropriate response.
        self.assertTrue(self.client.login(username='user', password='user'))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'package/edit_example.html')

        response = self.client.post(url, {
            'title': 'TEST TITLE',
            'url': 'http://github.com',
        })
        self.assertEqual(response.status_code, 302)
        e = PackageExample.objects.get(pk=id)
        self.assertEqual(e.title, 'TEST TITLE')

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
