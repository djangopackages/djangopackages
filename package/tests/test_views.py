import pytest
from django.contrib.auth.models import Permission, User
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from waffle.testutils import override_flag

from favorites.models import Favorite
from grid.models import Grid, GridPackage
from package.models import Category, FlaggedPackage, Package
from package.tests import initial_data
from profiles.models import Profile


@override_settings(RESTRICT_PACKAGE_EDITORS=False, RESTRICT_GRID_EDITORS=True)
class FunctionalPackageTest(TestCase):
    def setUp(self):
        self.data = initial_data.load()
        for user in User.objects.all():
            profile = Profile.objects.create(user=user)
            profile.save()

    def test_package_list_view(self):
        url = reverse("packages")
        with self.assertNumQueries(7):
            response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "package/package_list.html")
        packages = Package.objects.all()
        for p in packages:
            self.assertContains(response, p.title)

    @override_flag("enabled_packages_score_values", active=True)
    def test_package_detail_view_with_score(self):
        url = reverse("package", kwargs={"slug": "testability"})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "package/package_detail.html")
        self.assertContains(
            response,
            "Scores (0-100) add up six checks",
        )

    def test_package_detail_renders_readme_badge(self):
        url = reverse("package", kwargs={"slug": "testability"})
        response = self.client.get(url)

        self.assertContains(
            response,
            "[![Latest on Django Packages](https://img.shields.io/badge/PyPI-testability-tags-8c3c26.svg)](https://djangopackages.org/packages/p/testability/)",
        )

    @override_flag("enabled_packages_score_values", active=False)
    @pytest.mark.deprecated(
        """
        This test should be deleted after the `packages_score_values` checks
        are completely removed from the codebase.
        """
    )
    def test_package_detail_view_with_score_when_the_flag_is_disabled(self):
        url = reverse("package", kwargs={"slug": "testability"})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "package/package_detail.html")
        self.assertNotContains(
            response,
            "Scores (0-100) add up six checks",
        )

    def test_add_package_view(self):
        # this test has side effects, remove one of the fixture packages
        self.data.package3.delete()
        url = reverse("add_package")
        with self.assertNumQueries(0):
            response = self.client.get(url)

        # The response should be a redirect, since the user is not logged in.
        self.assertEqual(response.status_code, 302)

        # Once we log in the user, we should get back the appropriate response.
        self.assertTrue(self.client.login(username="user", password="user"))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "package/add_package.html")
        # The categories were asserted here, but the page has no category
        # list: it is the first step of the form and asks only for a repo
        # URL. The loop matched "App" against "Django Apps" in the keywords
        # meta tag, so it passed on any fixture and failed on a new category.
        count = Package.objects.count()
        # Use a unique slug and title to avoid IntegrityError
        unique_slug = "django-test-add-package-view"
        unique_title = "django test add package view"
        with self.assertNumQueries(15):
            response = self.client.post(
                url,
                {
                    "category": Category.objects.first().pk,
                    "repo_url": "https://github.com/django/django",
                    "slug": unique_slug,
                    "title": unique_title,
                    # Do not set pk/id, let DB auto-assign
                },
            )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Package.objects.count(), count + 1)

    def test_add_package_view_with_grid_slug(self):
        grid = Grid.objects.get(slug="testing")
        User.objects.get(username="user").user_permissions.add(
            Permission.objects.get(
                codename="add_gridpackage", content_type__app_label="grid"
            )
        )
        url = reverse("add_package") + f"?grid_slug={grid.slug}"

        # The response should be a redirect, since the user is not logged in.
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

        # Once we log in the user, we should get back the appropriate response.
        self.assertTrue(self.client.login(username="user", password="user"))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["grid"], grid)

        # Test form post
        # Use a unique slug and title to avoid IntegrityError
        unique_slug = "django-grid-test-add-package-view"
        unique_title = "django grid test add package view"
        with self.assertNumQueries(19):
            response = self.client.post(
                url,
                {
                    "category": Category.objects.first().pk,
                    "repo_url": "https://github.com/django/django-grid-test",
                    "slug": unique_slug,
                    "title": unique_title,
                },
            )
        self.assertEqual(response.status_code, 302)
        package = Package.objects.get(slug=unique_slug)
        self.assertTrue(GridPackage.objects.filter(grid=grid, package=package).exists())

    def test_edit_package_view(self):
        p = Package.objects.get(slug="testability")
        url = reverse("edit_package", kwargs={"slug": "testability"})
        with self.assertNumQueries(0):
            response = self.client.get(url)

        # The response should be a redirect, since the user is not logged in.
        self.assertEqual(response.status_code, 302)

        # Once we log in the user, we should get back the appropriate response.
        self.assertTrue(self.client.login(username="user", password="user"))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "package/edit_package.html")
        self.assertContains(response, p.title)
        self.assertContains(response, p.slug)

        # Make a test post
        with self.assertNumQueries(14):
            response = self.client.post(
                url,
                {
                    "category": str(Category.objects.first().pk),
                    "repo_url": "https://github.com/django/django",
                    "slug": p.slug,
                    "title": "TEST TITLE",
                },
            )
        self.assertEqual(response.status_code, 302)

        # Check that it actually changed the package
        p = Package.objects.get(slug="testability")
        self.assertEqual(p.title, "TEST TITLE")

    def test_flag_package_view(self):
        p = Package.objects.get(slug="testability")
        FlaggedPackage.objects.all().delete()
        url = reverse("flag", kwargs={"slug": p.slug})
        response = self.client.get(url)

        # The response should be a redirect, since the user is not logged in.
        self.assertEqual(response.status_code, 302)

        # Once we log in the user, we should get back the appropriate response.
        self.assertTrue(self.client.login(username="user", password="user"))
        with self.assertNumQueries(7):
            response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "package/package_flag_form.html")

        count = FlaggedPackage.objects.count()

        with self.assertNumQueries(7):
            response = self.client.post(
                url,
                {
                    "package": p,
                    "reason": "This is a test",
                },
            )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(FlaggedPackage.objects.count(), count + 1)

    def test_flag_approve_view(self):
        p = Package.objects.get(slug="testability")
        f = FlaggedPackage.objects.create(
            package=p, reason="This is a test", user=User.objects.get(username="user")
        )
        url = reverse("flag_approve", kwargs={"pk": f.pk})
        with self.assertNumQueries(0):
            response = self.client.get(url)

        # The response should be a redirect, since the user is not logged in.
        self.assertEqual(response.status_code, 302)

        # Logged in no-superuser should not be able to access this view
        self.assertTrue(self.client.login(username="user", password="user"))
        with self.assertNumQueries(6):
            response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

        # Once we log in the super user, we should get back the appropriate response.
        self.assertTrue(self.client.login(username="admin", password="admin"))
        with self.assertNumQueries(8):
            response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

        f = FlaggedPackage.objects.get(package=p)
        self.assertEqual(f.approved_flag, True)

    def test_flag_remove_view(self):
        p = Package.objects.get(slug="testability")
        f = FlaggedPackage.objects.create(
            package=p, reason="This is a test", user=User.objects.get(username="user")
        )
        url = reverse("flag_remove", kwargs={"pk": f.pk})
        with self.assertNumQueries(0):
            response = self.client.get(url)

        # The response should be a redirect, since the user is not logged in.
        self.assertEqual(response.status_code, 302)

        # Logged in no-superuser should not be able to access this view
        self.assertTrue(self.client.login(username="user", password="user"))
        with self.assertNumQueries(6):
            response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

        # Once we log in the super user, we should get back the appropriate response.
        self.assertTrue(self.client.login(username="admin", password="admin"))
        with self.assertNumQueries(8):
            response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

        self.assertRaises(
            FlaggedPackage.DoesNotExist, FlaggedPackage.objects.get, package=p
        )

    def test_usage_view(self):
        url = reverse("usage", kwargs={"slug": "testability", "action": "add"})
        response = self.client.get(url)

        # The response should be a redirect, since the user is not logged in.
        self.assertEqual(response.status_code, 302)

        user = User.objects.get(username="user")
        count = user.package_set.count()
        self.assertTrue(self.client.login(username="user", password="user"))

        # Now that the user is logged in, make sure that the number of packages
        # they use has increased by one.
        with self.assertNumQueries(6):
            response = self.client.get(url)
        self.assertEqual(count + 1, user.package_set.count())

        # Now we remove that same package from the user's list of used packages,
        # making sure that the total number has decreased by one.
        url = reverse("usage", kwargs={"slug": "testability", "action": "remove"})
        with self.assertNumQueries(5):
            response = self.client.get(url)
        self.assertEqual(count, user.package_set.count())

    def test_usage_button_on_package_page(self):
        url = reverse("package", kwargs={"slug": "testability"})

        # Anonymous: the count is shown with a login link, no toggle.
        response = self.client.get(url)
        self.assertContains(response, "Used by")
        self.assertNotContains(response, "I use this")

        # Logged in: the toggle, which flips after an htmx click.
        self.assertTrue(self.client.login(username="user", password="user"))
        response = self.client.get(url)
        self.assertContains(response, "I use this")
        self.assertTrue(response.context["is_using"] is False)

        toggle = reverse("usage", kwargs={"slug": "testability", "action": "add"})
        response = self.client.get(
            f"{toggle}?htmx=1&detail=1", headers={"hx-request": "true"}
        )
        self.assertContains(response, "Using")
        self.assertContains(response, 'id="usage-btn-')

        response = self.client.get(url)
        self.assertTrue(response.context["is_using"])
        self.assertContains(response, "Using")

    def test_most_liked_package_list_view(self):
        user = User.objects.get(username="user")
        admin = User.objects.get(username="admin")
        p1 = Package.objects.get(slug="testability")
        p2 = Package.objects.get(slug="supertester")

        # Create favorites
        Favorite.objects.create(package=p1, favorited_by=user)
        Favorite.objects.create(package=p1, favorited_by=admin)
        Favorite.objects.create(package=p2, favorited_by=user)

        url = reverse("liked_packages")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "package/package_archive.html")
        self.assertEqual(response.context["title"], "Most Liked Packages")

        packages = response.context["packages"]
        # Only packages with > 0 favorites should be shown
        self.assertEqual(len(packages), 2)
        # Ordered by most favorites
        self.assertEqual(packages[0], p1)
        self.assertEqual(packages[1], p2)
        self.assertEqual(packages[0].distinct_favs, 2)
        self.assertEqual(packages[1].distinct_favs, 1)

    def test_latest_package_list_view(self):
        url = reverse("latest_packages")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "package/package_archive.html")
        self.assertEqual(response.context["title"], "Latest Packages")

        packages = response.context["packages"]
        # initial_data loads 4 packages, all active
        self.assertEqual(len(packages), 4)

        # Test active filter: deprecate one package
        p = Package.objects.get(slug="testability")
        p.date_deprecated = timezone.now()
        p.save()

        response = self.client.get(url)
        packages = response.context["packages"]
        self.assertNotIn(p, packages)
        self.assertEqual(len(packages), 3)


@override_settings(RESTRICT_PACKAGE_EDITORS=True)
class PackagePermissionTest(TestCase):
    def setUp(self):
        self.data = initial_data.load()
        for user in User.objects.all():
            profile = Profile.objects.create(user=user)
            profile.save()

        self.test_add_url = reverse("add_package")
        self.test_edit_url = reverse("edit_package", kwargs={"slug": "testability"})
        self.login = self.client.login(username="user", password="user")
        self.user = User.objects.get(username="user")

    def test_login(self):
        self.assertTrue(self.login)

    def test_switch_permissions(self):
        with override_settings(RESTRICT_PACKAGE_EDITORS=False):
            with self.assertNumQueries(7):
                response = self.client.get(self.test_add_url)
            self.assertEqual(response.status_code, 200)

        with override_settings(RESTRICT_PACKAGE_EDITORS=True):
            with self.assertNumQueries(6):
                response = self.client.get(self.test_add_url)
            self.assertEqual(response.status_code, 403)

    def test_add_package_permission_fail(self):
        with self.assertNumQueries(8):
            response = self.client.get(self.test_add_url)
        self.assertEqual(response.status_code, 403)

    def test_add_package_permission_success(self):
        add_package_perm = Permission.objects.get(
            codename="add_package", content_type__app_label="package"
        )
        self.user.user_permissions.add(add_package_perm)
        with self.assertNumQueries(9):
            response = self.client.get(self.test_add_url)
        self.assertEqual(response.status_code, 200)

    def test_add_package_with_grid_slug_permission_fail(self):
        grid = Grid.objects.get(slug="testing")
        url = self.test_add_url + f"?grid_slug={grid.slug}"
        with self.assertNumQueries(8):
            response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_add_package_with_grid_slug_permission_success(self):
        grid = Grid.objects.get(slug="testing")
        url = self.test_add_url + f"?grid_slug={grid.slug}"
        add_package_perm = Permission.objects.get(
            codename="add_package", content_type__app_label="package"
        )
        self.user.user_permissions.add(add_package_perm)
        self.user.user_permissions.add(
            Permission.objects.get(
                codename="add_gridpackage", content_type__app_label="grid"
            )
        )
        with self.assertNumQueries(10):
            response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["grid"], grid)

    def test_add_package_with_grid_slug_requires_grid_permission(self):
        grid = Grid.objects.get(slug="testing")
        url = self.test_add_url + f"?grid_slug={grid.slug}"
        self.user.user_permissions.add(
            Permission.objects.get(
                codename="add_package", content_type__app_label="package"
            )
        )
        with override_settings(RESTRICT_GRID_EDITORS=True):
            response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context["grid"])

    def test_edit_package_permission_fail(self):
        with self.assertNumQueries(8):
            response = self.client.get(self.test_edit_url)
        self.assertEqual(response.status_code, 403)

    def test_edit_package_permission_success(self):
        edit_package_perm = Permission.objects.get(
            codename="change_package", content_type__app_label="package"
        )
        self.user.user_permissions.add(edit_package_perm)
        with self.assertNumQueries(11):
            response = self.client.get(self.test_edit_url)
        self.assertEqual(response.status_code, 200)


@override_settings(RESTRICT_PACKAGE_EDITORS=False)
class ValidateRepositoryURLViewTest(TestCase):
    def setUp(self):
        self.data = initial_data.load()
        for user in User.objects.all():
            Profile.objects.create(user=user)
        self.user = User.objects.get(username="user")
        self.url = reverse("validate_repo_url")

    def test_login_required(self):
        response = self.client.post(
            self.url, {"repo_url": "https://github.com/test/test"}
        )
        self.assertEqual(response.status_code, 302)

    def test_valid_new_repo(self):
        self.client.force_login(self.user)
        repo_url = "https://github.com/new/repo"
        response = self.client.post(self.url, {"repo_url": repo_url})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "partials/package_form.html")
        self.assertContains(response, 'value="repo"')
        self.assertContains(response, f'value="{repo_url}"')

    def test_valid_new_repo_with_grid_slug(self):
        self.client.force_login(self.user)
        repo_url = "https://github.com/new/repo-grid"
        grid_slug = "testing"
        url = self.url + f"?grid_slug={grid_slug}"
        response = self.client.post(url, {"repo_url": repo_url})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "partials/package_form.html")
        self.assertContains(response, f"grid_slug={grid_slug}")

    def test_existing_repo(self):
        self.client.force_login(self.user)
        package = Package.objects.first()
        response = self.client.post(self.url, {"repo_url": package.repo_url})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "partials/package_exists.html")
        self.assertContains(response, package.title)

    def test_invalid_repo_url(self):
        self.client.force_login(self.user)
        response = self.client.post(self.url, {"repo_url": "not-a-url"})
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "partials/repo_url_form.html")
        self.assertFormError(
            response.context["repo_form"],
            "repo_url",
            "Could not extract hostname from URL",
        )


def test_category_view(django_assert_num_queries, tp, initial_test_data):
    with django_assert_num_queries(6):
        response = tp.client.get("/categories/apps/")
    assert "apps" in str(response.content)


def test_grid_package_list(django_assert_num_queries, tp, initial_test_data):
    with django_assert_num_queries(8):
        url = tp.reverse("grid_packages", slug="testing")
        response = tp.client.get(url)

    assert response.status_code == 200


def test_package_version_list_view(db, django_assert_num_queries, tp, package_cms):
    url = tp.reverse("package_versions", slug=package_cms.slug)
    with django_assert_num_queries(2):
        response = tp.client.get(url)

    assert response.status_code == 200
    assert "partials/releases_table.html" in [t.name for t in response.templates]
