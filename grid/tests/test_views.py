from django.conf import settings
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User, Permission

from grid.models import Grid, Element, Feature, GridPackage
from package.models import Package

from grid.tests import data


class FunctionalGridTest(TestCase):
    def setUp(self):
        Grid.objects.all().delete()
        data.load()
        settings.RESTRICT_GRID_EDITORS = False

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


    def test_add_grid_view(self):
        Grid.objects.all().delete()
        url = reverse('add_grid')
        response = self.client.get(url)

        # The response should be a redirect, since the user is not logged in.
        self.assertEqual(response.status_code, 302)

        # Once we log in the user, we should get back the appropriate response.
        self.assertTrue(self.client.login(username='user', password='user'))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'grid/update_grid.html')

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
        self.assertTemplateUsed(response, 'grid/update_grid.html')

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
        Feature.objects.all().delete()  # Zero out the features

        url = reverse('add_feature', kwargs={'grid_slug': 'testing'})
        response = self.client.get(url)

        # The response should be a redirect, since the user is not logged in.
        self.assertEqual(response.status_code, 302)

        # Once we log in the user, we should get back the appropriate response.
        self.assertTrue(self.client.login(username='user', password='user'))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'grid/update_feature.html')

        # Test form post
        response = self.client.post(url, {
            'title': 'TEST TITLE',
            'description': 'Just a test description'
        }, follow=True)
        self.assertEqual(Feature.objects.count(), 1)
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
        self.assertTemplateUsed(response, 'grid/update_feature.html')

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
        self.client.get(url)
        self.assertEqual(count, Feature.objects.count())

        # Once we log in with the appropriate user, the request should delete
        # the given feature, reducing the count by one.
        self.assertTrue(self.client.login(username='cleaner', password='cleaner'))
        self.client.get(url)
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

        # Confirm 404 if grid IDs differ
        url = reverse('edit_element', kwargs={'feature_id': '1', 'package_id': '4'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_add_grid_package_view(self):
        # this test has side effects. Remove GridPackage 1 and 3
        GridPackage.objects.get(pk=1).delete()
        GridPackage.objects.get(pk=3).delete()
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
        Package.objects.all().delete()
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
        self.client.get(url)
        self.assertEqual(count, GridPackage.objects.count())

        # Once we log in with the appropriate user, the request should delete
        # the given feature, reducing the count by one.
        self.assertTrue(self.client.login(username='cleaner', password='cleaner'))
        self.client.get(url)
        self.assertEqual(count - 1, GridPackage.objects.count())


class RegressionGridTest(TestCase):
    def setUp(self):
        data.load()
        settings.RESTRICT_GRID_EDITORS = False

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


class GridPermissionTest(TestCase):
    def setUp(self):
        data.load()
        settings.RESTRICT_GRID_EDITORS = True
        self.test_add_url = reverse('add_grid')
        self.test_edit_url = reverse('edit_grid', kwargs={'slug': 'testing'})
        self.login = self.client.login(username='user', password='user')
        self.user = User.objects.get(username='user')

    def test_add_grid_permission_fail(self):
        response = self.client.get(self.test_add_url)
        self.assertEqual(response.status_code, 403)

    def test_add_grid_permission_success(self):
        add_grid_perm = Permission.objects.get(codename='add_grid',
            content_type__app_label='grid')
        self.user.user_permissions.add(add_grid_perm)
        response = self.client.get(self.test_add_url)
        self.assertEqual(response.status_code, 200)

    def test_edit_grid_permission_fail(self):
        response = self.client.get(self.test_edit_url)
        self.assertEqual(response.status_code, 403)

    def test_edit_grid_permission_success(self):
        edit_grid_perm = Permission.objects.get(codename='change_grid',
                content_type__app_label='grid')
        self.user.user_permissions.add(edit_grid_perm)
        response = self.client.get(self.test_edit_url)
        self.assertEqual(response.status_code, 200)


class GridPackagePermissionTest(TestCase):
    def setUp(self):
        data.load()
        settings.RESTRICT_GRID_EDITORS = True
        self.test_add_url = reverse('add_grid_package',
                                    kwargs={'grid_slug': 'testing'})
        self.test_add_new_url = reverse('add_new_grid_package',
                                        kwargs={'grid_slug': 'testing'})
        self.test_delete_url = reverse('delete_grid_package',
                                       kwargs={'id': '1'})
        self.login = self.client.login(username='user', password='user')
        self.user = User.objects.get(username='user')

    def test_login(self):
        self.assertTrue(self.login)

    def test_add_grid_package_permission_fail(self):
        response = self.client.get(self.test_add_url)
        self.assertEqual(response.status_code, 403)

    def test_add_grid_package_permission_success(self):
        add_grid_perm = Permission.objects.get(codename='add_gridpackage',
                content_type__app_label='grid')
        self.user.user_permissions.add(add_grid_perm)
        response = self.client.get(self.test_add_url)
        self.assertEqual(response.status_code, 200)

    def test_add_new_grid_package_permission_fail(self):
        response = self.client.get(self.test_add_new_url)
        self.assertEqual(response.status_code, 403)

    def test_add_new_grid_package_permission_success(self):
        add_new_grid_perm = Permission.objects.get(codename='add_gridpackage',
                content_type__app_label='grid')
        self.user.user_permissions.add(add_new_grid_perm)
        response = self.client.get(self.test_add_new_url)
        self.assertEqual(response.status_code, 200)

    def test_delete_grid_package_permission_fail(self):
        response = self.client.get(self.test_delete_url)
        self.assertEqual(response.status_code, 302)

    def test_delete_grid_package_permission_success(self):
        delete_grid_perm = Permission.objects.get(codename='delete_gridpackage',
                content_type__app_label='grid')
        self.user.user_permissions.add(delete_grid_perm)
        response = self.client.get(self.test_delete_url)
        self.assertEqual(response.status_code, 302)


class GridFeaturePermissionTest(TestCase):
    def setUp(self):
        data.load()
        settings.RESTRICT_GRID_EDITORS = True
        self.test_add_url = reverse('add_feature',
                                    kwargs={'grid_slug': 'testing'})
        self.test_edit_url = reverse('edit_feature', kwargs={'id': '1'})
        self.test_delete_url = reverse('delete_feature',  kwargs={'id': '1'})
        self.login = self.client.login(username='user', password='user')
        self.user = User.objects.get(username='user')

    def test_add_feature_permission_fail(self):
        response = self.client.get(self.test_add_url)
        self.assertEqual(response.status_code, 403)

    def test_add_feature_permission_success(self):
        add_feature = Permission.objects.get(codename='add_feature',
                content_type__app_label='grid')
        self.user.user_permissions.add(add_feature)
        response = self.client.get(self.test_add_url)
        self.assertEqual(response.status_code, 200)

    def test_edit_feature_permission_fail(self):
        response = self.client.get(self.test_edit_url)
        self.assertEqual(response.status_code, 403)

    def test_edit_feature_permission_success(self):
        edit_feature = Permission.objects.get(codename='change_feature',
                content_type__app_label='grid')
        self.user.user_permissions.add(edit_feature)
        response = self.client.get(self.test_edit_url)
        self.assertEqual(response.status_code, 200)

    def test_delete_feature_permission_fail(self):
        response = self.client.get(self.test_delete_url)
        self.assertEqual(response.status_code, 302)

    def test_delete_feature_permission_success(self):
        delete_feature = Permission.objects.get(codename='delete_feature',
                content_type__app_label='grid')
        self.user.user_permissions.add(delete_feature)
        response = self.client.get(self.test_delete_url)
        self.assertEqual(response.status_code, 302)


class GridElementPermissionTest(TestCase):
    def setUp(self):
        data.load()
        settings.RESTRICT_GRID_EDITORS = True
        self.test_edit_url = reverse('edit_element',
                                     kwargs={'feature_id': '1',
                                             'package_id': '1'})
        self.login = self.client.login(username='user', password='user')
        self.user = User.objects.get(username='user')

    def test_edit_element_permission_fail(self):
        response = self.client.get(self.test_edit_url)
        self.assertEqual(response.status_code, 403)

    def test_edit_element_permission_success(self):
        edit_element = Permission.objects.get(codename='change_element',
                content_type__app_label='grid')
        self.user.user_permissions.add(edit_element)
        response = self.client.get(self.test_edit_url)
        self.assertEqual(response.status_code, 200)
