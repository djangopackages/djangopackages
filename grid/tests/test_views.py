from datetime import datetime, timedelta

import pytest
from django.conf import settings
from django.contrib.auth.models import Permission, User
from django.core.cache import cache
from django.db import connection
from django.test import TestCase, override_settings
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone
from waffle.testutils import override_flag

from grid.models import Element, Feature, Grid, GridPackage
from grid.tests import data
from package.models import Category, Package, Version


class FunctionalGridTest(TestCase):
    def setUp(self):
        Grid.objects.all().delete()
        data.load()
        settings.RESTRICT_GRID_EDITORS = False
        cache.clear()

    def test_grid_list_view(self):
        url = reverse("grids")
        with self.assertNumQueries(3):
            response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "grid/grid_list.html")

    @override_flag("enabled_packages_score_values", active=True)
    def test_grid_detail_view(self):
        url = reverse("grid", kwargs={"slug": "testing"})

        with CaptureQueriesContext(connection) as ctx:
            response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "grid/grid_detail.html")

        # The view is intentionally query-heavy when cold, but should remain
        # bounded.
        assert len(ctx) <= 12

        # Second request should reuse cached comparison payload.
        with CaptureQueriesContext(connection) as ctx2:
            response2 = self.client.get(url)
        self.assertEqual(response2.status_code, 200)
        assert len(ctx2) < len(ctx)

    def test_add_grid_view(self):
        Grid.objects.all().delete()
        url = reverse("add_grid")
        with self.assertNumQueries(0):
            response = self.client.get(url)

        # The response should be a redirect, since the user is not logged in.
        self.assertEqual(response.status_code, 302)

        # Once we log in the user, we should get back the appropriate response.
        self.assertTrue(self.client.login(username="user", password="user"))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "grid/add_grid.html")

        # Test form post
        count = Grid.objects.count()
        response = self.client.post(
            url,
            {
                "title": "TEST TITLE",
                "slug": "test-title",
                "description": "Just a test description",
            },
            follow=True,
        )
        self.assertEqual(Grid.objects.count(), count + 1)
        self.assertContains(response, "TEST TITLE")

    def test_edit_grid_view(self):
        url = reverse("edit_grid", kwargs={"slug": "testing"})
        response = self.client.get(url)

        # The response should be a redirect, since the user is not logged in.
        self.assertEqual(response.status_code, 302)

        # Once we log in the user, we should get back the appropriate response.
        self.assertTrue(self.client.login(username="user", password="user"))
        with self.assertNumQueries(5):
            response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "grid/add_grid.html")

        # Test form post
        count = Grid.objects.count()
        response = self.client.post(
            url,
            {
                "title": "TEST TITLE",
                "slug": "testing",
                "description": "Just a test description",
            },
            follow=True,
        )
        self.assertEqual(Grid.objects.count(), count)
        self.assertContains(response, "TEST TITLE")

    @override_flag("enabled_packages_score_values", active=True)
    def test_grid_detail_view_with_score(self):
        url = reverse("grid", kwargs={"slug": "testing"})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "grid/grid_detail.html")

        self.assertContains(response, "Scores (0-100) are based on Repository stars")

    @override_flag("enabled_packages_score_values", active=False)
    @pytest.mark.deprecated(
        """
        This test should be deleted after the `packages_score_values` checks
        are completely removed from the codebase.
        """
    )
    def test_grid_detail_view_with_score_when_the_flag_is_disabled(self):
        url = reverse("grid", kwargs={"slug": "testing"})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "grid/grid_detail.html")

        self.assertNotContains(
            response,
            "Scores (0-100) are based on Repository stars",
        )

    def test_add_feature_view(self):
        Feature.objects.all().delete()  # Zero out the features

        url = reverse("add_feature", kwargs={"grid_slug": "testing"})
        response = self.client.get(url)

        # The response should be a redirect, since the user is not logged in.
        self.assertEqual(response.status_code, 302)

        # Once we log in the user, we should get back the appropriate response.
        self.assertTrue(self.client.login(username="user", password="user"))
        with self.assertNumQueries(7):
            response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "grid/add_feature.html")

        # Test form post
        response = self.client.post(
            url,
            {"title": "TEST TITLE", "description": "Just a test description"},
            follow=True,
        )
        self.assertEqual(Feature.objects.count(), 1)
        self.assertTrue(Feature.objects.filter(title="TEST TITLE").exists())

    def test_edit_feature_view(self):
        url = reverse("edit_feature", kwargs={"id": "1"})
        response = self.client.get(url)

        # The response should be a redirect, since the user is not logged in.
        self.assertEqual(response.status_code, 302)

        # Once we log in the user, we should get back the appropriate response.
        self.assertTrue(self.client.login(username="user", password="user"))
        with self.assertNumQueries(6):
            response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "grid/add_feature.html")

        # Test form post
        count = Feature.objects.count()
        response = self.client.post(
            url,
            {"title": "TEST TITLE", "description": "Just a test description"},
            follow=True,
        )
        self.assertEqual(Feature.objects.count(), count)
        self.assertTrue(Feature.objects.filter(title="TEST TITLE").exists())

    def test_delete_feature_view(self):
        count = Feature.objects.count()

        # Since this user doesn't have the appropriate permissions, none of the
        # features should be deleted (thus the count should be the same).
        self.assertTrue(self.client.login(username="user", password="user"))
        url = reverse("delete_feature", kwargs={"id": "1"})
        with self.assertNumQueries(6):
            self.client.post(url)
        self.assertEqual(count, Feature.objects.count())

        # Once we log in with the appropriate user, the request should delete
        # the given feature, reducing the count by one.
        self.assertTrue(self.client.login(username="cleaner", password="cleaner"))
        self.client.post(url)
        self.assertEqual(Feature.objects.count(), count - 1)

    def test_edit_element_view(self):
        url = reverse(
            "edit_element",
            kwargs={"grid_slug": "testing", "feature_id": "1", "package_id": "1"},
        )
        with self.assertNumQueries(0):
            response = self.client.get(url)

        # The response should be a redirect, since the user is not logged in.
        self.assertEqual(response.status_code, 302)

        # Once we log in the user, we should get back the appropriate response.
        self.assertTrue(self.client.login(username="user", password="user"))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "grid/edit_element.html")

        # Test form post
        count = Element.objects.count()
        response = self.client.post(
            url,
            {
                "text": "Some random text",
            },
            follow=True,
        )
        self.assertEqual(Element.objects.count(), count)

        # Confirm 404 if grid IDs differ
        url = reverse(
            "edit_element",
            kwargs={"grid_slug": "testing", "feature_id": "1", "package_id": "4"},
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_add_grid_package_view(self):
        # this test has side effects. Remove GridPackage 1 and 3
        GridPackage.objects.get(pk=1).delete()
        GridPackage.objects.get(pk=3).delete()
        url = reverse("add_grid_package", kwargs={"grid_slug": "testing"})
        response = self.client.get(url)

        # The response should be a redirect, since the user is not logged in.
        self.assertEqual(response.status_code, 302)

        # Once we log in the user, we should get back the appropriate response.
        self.assertTrue(self.client.login(username="user", password="user"))
        with self.assertNumQueries(5):
            response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "grid/add_grid_package.html")

        # Test form post for existing grid package
        response = self.client.post(
            url,
            {
                "package": 2,
            },
        )
        self.assertContains(
            response, "&#x27;Supertester&#x27; is already in this grid."
        )
        # Test form post for new grid package
        count = GridPackage.objects.count()
        response = self.client.post(
            url,
            {
                "package": 4,
            },
            follow=True,
        )
        self.assertEqual(GridPackage.objects.count(), count + 1)
        self.assertContains(response, "Another Test")

    def test_ajax_grid_search_view(self):
        url = reverse("ajax_grid_search") + "?q=Testing&package_id=4"
        with self.assertNumQueries(2):
            response = self.client.get(url)
        self.assertContains(response, "Testing")

    def test_delete_gridpackage_view(self):
        count = GridPackage.objects.count()

        # Since this user doesn't have the appropriate permissions, none of the
        # features should be deleted (thus the count should be the same).
        self.assertTrue(self.client.login(username="user", password="user"))
        url = reverse(
            "delete_grid_package", kwargs={"grid_slug": "testing", "package_id": "1"}
        )
        with self.assertNumQueries(6):
            self.client.post(url)
        self.assertEqual(count, GridPackage.objects.count())

        # Once we log in with the appropriate user, the request should delete
        # the given feature, reducing the count by one.
        self.assertTrue(self.client.login(username="cleaner", password="cleaner"))
        self.client.post(url)
        self.assertEqual(count - 1, GridPackage.objects.count())


class RegressionGridTest(TestCase):
    def setUp(self):
        data.load()
        settings.RESTRICT_GRID_EDITORS = False

    def test_edit_element_view_for_nonexistent_elements(self):
        """Make sure that attempts to edit nonexistent elements succeed."""
        # Delete the element for the specified feature and package.
        element, created = Element.objects.get_or_create(feature=1, grid_package=1)
        element.delete()

        # Log in the test user and attempt to edit the element.
        self.assertTrue(self.client.login(username="user", password="user"))

        url = reverse(
            "edit_element",
            kwargs={"grid_slug": "testing", "feature_id": "1", "package_id": "1"},
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "grid/edit_element.html")


class GridPermissionTest(TestCase):
    def setUp(self):
        data.load()
        settings.RESTRICT_GRID_EDITORS = True
        self.test_add_url = reverse("add_grid")
        self.test_edit_url = reverse("edit_grid", kwargs={"slug": "testing"})
        self.login = self.client.login(username="user", password="user")
        self.user = User.objects.get(username="user")

    def test_add_grid_permission_fail(self):
        response = self.client.get(self.test_add_url)
        self.assertEqual(response.status_code, 403)

    def test_add_grid_permission_success(self):
        add_grid_perm = Permission.objects.get(
            codename="add_grid", content_type__app_label="grid"
        )
        self.user.user_permissions.add(add_grid_perm)
        response = self.client.get(self.test_add_url)
        self.assertEqual(response.status_code, 200)

    def test_edit_grid_permission_fail(self):
        response = self.client.get(self.test_edit_url)
        self.assertEqual(response.status_code, 403)

    def test_edit_grid_permission_success(self):
        edit_grid_perm = Permission.objects.get(
            codename="change_grid", content_type__app_label="grid"
        )
        self.user.user_permissions.add(edit_grid_perm)
        response = self.client.get(self.test_edit_url)
        self.assertEqual(response.status_code, 200)


class GridPackagePermissionTest(TestCase):
    def setUp(self):
        data.load()
        settings.RESTRICT_GRID_EDITORS = True
        self.test_add_url = reverse("add_grid_package", kwargs={"grid_slug": "testing"})
        self.test_delete_url = reverse(
            "delete_grid_package", kwargs={"grid_slug": "testing", "package_id": "1"}
        )
        self.login = self.client.login(username="user", password="user")
        self.user = User.objects.get(username="user")

    def test_login(self):
        self.assertTrue(self.login)

    def test_add_grid_package_permission_fail(self):
        response = self.client.get(self.test_add_url)
        self.assertEqual(response.status_code, 403)

    def test_add_grid_package_permission_success(self):
        add_grid_perm = Permission.objects.get(
            codename="add_gridpackage", content_type__app_label="grid"
        )
        self.user.user_permissions.add(add_grid_perm)
        response = self.client.get(self.test_add_url)
        self.assertEqual(response.status_code, 200)

    def test_delete_grid_package_permission_fail(self):
        response = self.client.get(self.test_delete_url)
        self.assertEqual(response.status_code, 403)

    def test_delete_grid_package_permission_success(self):
        delete_grid_perm = Permission.objects.get(
            codename="delete_gridpackage", content_type__app_label="grid"
        )
        self.user.user_permissions.add(delete_grid_perm)
        response = self.client.post(self.test_delete_url)
        self.assertEqual(response.status_code, 302)


class GridFeaturePermissionTest(TestCase):
    def setUp(self):
        data.load()
        settings.RESTRICT_GRID_EDITORS = True
        self.test_add_url = reverse("add_feature", kwargs={"grid_slug": "testing"})
        self.test_edit_url = reverse("edit_feature", kwargs={"id": "1"})
        self.test_delete_url = reverse("delete_feature", kwargs={"id": "1"})
        self.login = self.client.login(username="user", password="user")
        self.user = User.objects.get(username="user")

    def test_add_feature_permission_fail(self):
        response = self.client.get(self.test_add_url)
        self.assertEqual(response.status_code, 403)

    def test_add_feature_permission_success(self):
        add_feature = Permission.objects.get(
            codename="add_feature", content_type__app_label="grid"
        )
        self.user.user_permissions.add(add_feature)
        response = self.client.get(self.test_add_url)
        self.assertEqual(response.status_code, 200)

    def test_edit_feature_permission_fail(self):
        response = self.client.get(self.test_edit_url)
        self.assertEqual(response.status_code, 403)

    def test_edit_feature_permission_success(self):
        edit_feature = Permission.objects.get(
            codename="change_feature", content_type__app_label="grid"
        )
        self.user.user_permissions.add(edit_feature)
        response = self.client.get(self.test_edit_url)
        self.assertEqual(response.status_code, 200)

    def test_delete_feature_permission_fail(self):
        response = self.client.get(self.test_delete_url)
        self.assertEqual(response.status_code, 403)

    def test_delete_feature_permission_success(self):
        delete_feature = Permission.objects.get(
            codename="delete_feature", content_type__app_label="grid"
        )
        self.user.user_permissions.add(delete_feature)
        response = self.client.post(self.test_delete_url)
        self.assertEqual(response.status_code, 302)


class GridElementPermissionTest(TestCase):
    def setUp(self):
        data.load()
        settings.RESTRICT_GRID_EDITORS = True
        self.test_edit_url = reverse(
            "edit_element",
            kwargs={"grid_slug": "testing", "feature_id": "1", "package_id": "1"},
        )
        self.login = self.client.login(username="user", password="user")
        self.user = User.objects.get(username="user")

    def test_edit_element_permission_fail(self):
        response = self.client.get(self.test_edit_url)
        self.assertEqual(response.status_code, 403)

    def test_edit_element_permission_success(self):
        edit_element = Permission.objects.get(
            codename="change_element", content_type__app_label="grid"
        )
        self.user.user_permissions.add(edit_element)
        response = self.client.get(self.test_edit_url)
        self.assertEqual(response.status_code, 200)


class GridDetailQueryCountTest(TestCase):
    """Test that grid_detail view has constant query count regardless of package count."""

    @classmethod
    def setUpTestData(cls):
        # Use a fixed reference time that matches the frozen time in conftest.py
        # The conftest freezes time to datetime(2022, 2, 22, 2, 22)
        reference_time = timezone.make_aware(datetime(2022, 2, 22, 2, 22))

        # Create category
        cls.category = Category.objects.create(
            slug="test-apps",
            title="Test Apps",
            description="Test category",
        )

        # Create grid
        cls.grid = Grid.objects.create(
            title="Large Grid Test",
            slug="large-grid-test",
            description="A grid with many packages for query count testing",
        )

        # Create 100 packages and add them to the grid
        cls.packages = []
        cls.grid_packages = []

        for i in range(100):
            package = Package.objects.create(
                title=f"Test Package {i}",
                slug=f"test-package-{i}",
                category=cls.category,
                repo_url=f"https://github.com/test/test-package-{i}",
                repo_description=f"Description for test package {i}",
                repo_watchers=i * 10,
                repo_forks=i * 5,
                pypi_downloads=i * 100,
                participants=f"user{i},user{i + 1}",
                score=50,  # Ensure it passes PACKAGE_SCORE_MIN filter
                last_commit_date=reference_time - timedelta(days=30),
            )
            cls.packages.append(package)

            grid_package = GridPackage.objects.create(
                grid=cls.grid,
                package=package,
            )
            cls.grid_packages.append(grid_package)

            # Add some versions for each package
            for j in range(2):
                Version.objects.create(
                    package=package,
                    number=f"{j}.0.0",
                    upload_time=reference_time - timedelta(days=j * 60),
                    development_status=5 if j == 0 else 3,
                    supports_python3=True,
                )

        # Create some features for the grid
        cls.features = []
        for i in range(5):
            feature = Feature.objects.create(
                grid=cls.grid,
                title=f"Feature {i}",
                description=f"Description for feature {i}",
            )
            cls.features.append(feature)

        # Create some elements (feature values for packages)
        for feature in cls.features:
            for grid_package in cls.grid_packages[
                :20
            ]:  # Elements for first 20 packages
                Element.objects.create(
                    feature=feature,
                    grid_package=grid_package,
                    text="Yes",
                )

    @override_flag("enabled_packages_score_values", active=True)
    def test_grid_detail_query_count_with_100_packages(self):
        """Test that query count is constant (not N+1) with 100 packages."""
        url = reverse("grid", kwargs={"slug": "large-grid-test"})

        # Capture actual query count
        with CaptureQueriesContext(connection) as context:
            response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

        # GridDetailView now caps packages at max_packages (10)
        self.assertEqual(len(response.context["packages"]), 10)
        self.assertEqual(response.context["total_package_count"], 100)
        self.assertTrue(response.context["has_more_packages"])

        query_count = len(context)

        # Assert query count is reasonable (not N+1)
        # Current baseline is ~10 queries.
        # If we had N+1 issues, we'd see 100+ queries.
        self.assertLessEqual(
            query_count,
            15,
            f"Query count ({query_count}) is too high, possible N+1 issue. "
            f"Queries: {[q['sql'][:100] for q in context]}",
        )

    @override_flag("enabled_packages_score_values", active=True)
    def test_grid_detail_query_count_with_filters(self):
        """Test query count remains constant when filters are applied."""
        url = reverse("grid", kwargs={"slug": "large-grid-test"})

        # Test with search filter
        with CaptureQueriesContext(connection) as context:
            response = self.client.get(url, {"q": "Package 5"})
        self.assertEqual(response.status_code, 200)
        self.assertLessEqual(
            len(context), 15, "Query count too high with search filter"
        )

        # Test with sort filter
        with CaptureQueriesContext(connection) as context:
            response = self.client.get(url, {"sort": "title"})
        self.assertEqual(response.status_code, 200)
        self.assertLessEqual(len(context), 15, "Query count too high with sort filter")


class GridShowFeaturesTest(TestCase):
    """Test that features are shown/hidden based on DISPLAY_GRID_FEATURES setting."""

    def setUp(self):
        cache.clear()
        self.category = Category.objects.create(
            slug="test-category",
            title="Test Category",
            description="Test category",
        )
        self.grid = Grid.objects.create(
            title="Show Features Test Grid",
            slug="show-features-test",
            description="Grid for testing show_features behavior",
        )
        # Create features for the grid
        self.feature = Feature.objects.create(
            grid=self.grid,
            title="Test Feature",
            description="A test feature",
        )

    def _create_packages(self, count):
        """Helper to create packages and add them to the grid."""
        for i in range(count):
            package = Package.objects.create(
                title=f"Package {i}",
                slug=f"package-{i}",
                category=self.category,
                repo_url=f"https://github.com/test/package-{i}",
                score=50,
            )
            GridPackage.objects.create(grid=self.grid, package=package)

    @override_flag("enabled_packages_score_values", active=True)
    @override_settings(DISPLAY_GRID_FEATURES=True)
    def test_show_features_true_when_enabled_and_packages_at_max(self):
        self._create_packages(8)
        url = reverse("grid", kwargs={"slug": "show-features-test"})

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["show_features"])
        self.assertEqual(response.context["total_package_count"], 8)
        self.assertContains(response, "Test Feature")

    @override_flag("enabled_packages_score_values", active=True)
    @override_settings(DISPLAY_GRID_FEATURES=True)
    def test_show_features_true_when_enabled_and_packages_below_max(self):
        self._create_packages(3)
        url = reverse("grid", kwargs={"slug": "show-features-test"})

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["show_features"])
        self.assertEqual(response.context["total_package_count"], 3)
        self.assertContains(response, "Test Feature")

    @override_flag("enabled_packages_score_values", active=True)
    @override_settings(DISPLAY_GRID_FEATURES=True)
    def test_show_features_true_when_enabled_and_packages_exceed_max(self):
        self._create_packages(9)
        url = reverse("grid", kwargs={"slug": "show-features-test"})

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["show_features"])
        self.assertEqual(response.context["total_package_count"], 9)
        self.assertContains(response, "Test Feature")

    @override_flag("enabled_packages_score_values", active=True)
    @override_settings(DISPLAY_GRID_FEATURES=True)
    def test_show_features_true_with_many_packages(self):
        self._create_packages(20)
        url = reverse("grid", kwargs={"slug": "show-features-test"})

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["show_features"])
        self.assertEqual(response.context["total_package_count"], 20)
        # Should still only display max_packages (10) packages
        self.assertEqual(len(response.context["packages"]), 10)
        self.assertTrue(response.context["has_more_packages"])
        self.assertContains(response, "Test Feature")

    @override_flag("enabled_packages_score_values", active=True)
    @override_settings(DISPLAY_GRID_FEATURES=False)
    def test_show_features_false_when_setting_disabled(self):
        self._create_packages(3)

        url = reverse("grid", kwargs={"slug": "show-features-test"})

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["show_features"])
        self.assertEqual(response.context["total_package_count"], 3)
        self.assertNotContains(response, "Test Feature")
