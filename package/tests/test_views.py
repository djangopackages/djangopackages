from django.conf import settings
from django.contrib.auth.models import User, Permission
from django.urls import reverse
from django.test import TestCase

from package.models import Category, Package, PackageExample
from package.tests import initial_data

from profiles.models import Profile


class FunctionalPackageTest(TestCase):
    def setUp(self):
        initial_data.load()
        for user in User.objects.all():
            profile = Profile.objects.create(user=user)
            profile.save()
        settings.RESTRICT_PACKAGE_EDITORS = False
        settings.RESTRICT_GRID_EDITORS = True

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
        for e in p.active_examples:
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
        # this test has side effects, remove Package 3
        Package.objects.get(pk=3).delete()
        url = reverse('add_package')
        response = self.client.get(url)

        # The response should be a redirect, since the user is not logged in.
        self.assertEqual(response.status_code, 302)

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
            'repo_url': 'https://github.com/django/django',
            'slug': 'django',
            'title': 'django',
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Package.objects.count(), count + 1)

    def test_edit_package_view(self):
        p = Package.objects.get(slug='testability')
        url = reverse('edit_package', kwargs={'slug': 'testability'})
        response = self.client.get(url)

        # The response should be a redirect, since the user is not logged in.
        self.assertEqual(response.status_code, 302)

        # Once we log in the user, we should get back the appropriate response.
        self.assertTrue(self.client.login(username='user', password='user'))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        #print(response._container)
        self.assertTemplateUsed(response, 'package/package_form.html')
        self.assertContains(response, p.title)
        self.assertContains(response, p.slug)

        # Make a test post
        response = self.client.post(url, {
            'category': str(Category.objects.all()[0].pk),
            'repo_url': 'https://github.com/django/django',
            'slug': p.slug,
            'title': 'TEST TITLE',
        })
        self.assertEqual(response.status_code, 302)

        # Check that it actually changed the package
        p = Package.objects.get(slug='testability')
        self.assertEqual(p.title, 'TEST TITLE')

    def test_add_example_view(self):
        PackageExample.objects.all().delete()
        url = reverse('add_example', kwargs={'slug': 'testability'})
        response = self.client.get(url)

        # The response should be a redirect, since the user is not logged in.
        self.assertEqual(response.status_code, 302)

        # Once we log in the user, we should get back the appropriate response.
        self.assertTrue(self.client.login(username='user', password='user'))
        user = User.objects.get(username='user')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'package/add_example.html')

        id_list = list(PackageExample.objects.values_list('id', flat=True))
        response = self.client.post(url, {
            'title': 'TEST TITLE',
            'url': 'https://github.com',
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(PackageExample.objects.count(), len(id_list) + 1)

        recently_added = PackageExample.objects.exclude(id__in=id_list).first()
        self.assertEqual(recently_added.created_by.id, user.id)

    def test_edit_example_view(self):
        user = User.objects.get(username='user')
        e = PackageExample.objects.exclude(created_by=user).first()
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
        self.assertNotContains(response, 'example-delete-btn')

        response = self.client.post(url, {
            'title': 'TEST TITLE',
            'url': 'https://github.com',
        })
        self.assertEqual(response.status_code, 302)
        e = PackageExample.objects.get(pk=id)
        self.assertEqual(e.title, 'TEST TITLE')

        deletable_e = PackageExample.objects.filter(created_by=user).first()
        url = reverse('edit_example', kwargs={'slug': e.package.slug,
            'id': deletable_e.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'example-delete-btn')

    def test_delete_example_view(self):
        user = User.objects.get(username='user')
        e = PackageExample.objects.filter(created_by=user).first()
        other_e = PackageExample.objects.exclude(created_by=user).exclude(created_by=None).first()
        noone_e = PackageExample.objects.filter(created_by=None).first()

        url = reverse('delete_example', kwargs={'slug': e.package.slug,
            'id': e.pk})
        other_url = reverse('delete_example', kwargs={'slug': other_e.package.slug,
            'id': other_e.pk})
        noone_url = reverse('delete_example', kwargs={'slug': noone_e.package.slug,
            'id': noone_e.pk})

        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

        self.assertTrue(self.client.login(username='user', password='user'))

        response = self.client.get(other_url)
        self.assertEqual(response.status_code, 403)
        response = self.client.get(noone_url)
        self.assertEqual(response.status_code, 403)

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        confirm_url = reverse('confirm_delete_example', kwargs={'slug': e.package.slug,
            'id': e.pk})
        confirm_other_url = reverse('confirm_delete_example', kwargs={'slug': other_e.package.slug,
            'id': other_e.pk})
        confirm_noone_url = reverse('delete_example', kwargs={'slug': noone_e.package.slug,
            'id': noone_e.pk})

        response = self.client.post(confirm_other_url)
        self.assertEqual(response.status_code, 403)
        response = self.client.post(confirm_noone_url)
        self.assertEqual(response.status_code, 403)

        response = self.client.post(confirm_url)
        self.assertEqual(response.status_code, 302)
        self.assertRaises(PackageExample.DoesNotExist, PackageExample.objects.get, id=e.id)

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


class PackagePermissionTest(TestCase):
    def setUp(self):
        initial_data.load()
        for user in User.objects.all():
            profile = Profile.objects.create(user=user)
            profile.save()

        settings.RESTRICT_PACKAGE_EDITORS = True
        self.test_add_url = reverse('add_package')
        self.test_edit_url = reverse('edit_package',
                                     kwargs={'slug': 'testability'})
        self.login = self.client.login(username='user', password='user')
        self.user = User.objects.get(username='user')

    def test_login(self):
        self.assertTrue(self.login)

    def test_switch_permissions(self):
        settings.RESTRICT_PACKAGE_EDITORS = False
        response = self.client.get(self.test_add_url)
        self.assertEqual(response.status_code, 200)
        settings.RESTRICT_PACKAGE_EDITORS = True
        response = self.client.get(self.test_add_url)
        self.assertEqual(response.status_code, 403)

    def test_add_package_permission_fail(self):
        response = self.client.get(self.test_add_url)
        self.assertEqual(response.status_code, 403)

    def test_add_package_permission_success(self):
        add_package_perm = Permission.objects.get(codename="add_package",
                content_type__app_label='package')
        self.user.user_permissions.add(add_package_perm)
        response = self.client.get(self.test_add_url)
        self.assertEqual(response.status_code, 200)

    def test_edit_package_permission_fail(self):
        response = self.client.get(self.test_edit_url)
        self.assertEqual(response.status_code, 403)

    def test_edit_package_permission_success(self):
        edit_package_perm = Permission.objects.get(codename="change_package",
                content_type__app_label='package')
        self.user.user_permissions.add(edit_package_perm)
        response = self.client.get(self.test_edit_url)
        self.assertEqual(response.status_code, 200)

class CategoryTest(TestCase):
    def setUp(self):
        initial_data.load()

    def test_category_view(self):
        response = self.client.get('/categories/apps/')
        self.assertContains(response, 'apps')
