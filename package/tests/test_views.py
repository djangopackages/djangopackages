import pytest
from django.conf import settings
from django.contrib.auth.models import Permission, User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from waffle.testutils import override_flag

from favorites.models import Favorite
from grid.models import Grid, GridPackage
from package.models import Category, FlaggedPackage, Package, PackageExample
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
        url = reverse("packages")
        with self.assertNumQueries(5):
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
            "Scores (0-100) are based on Repository stars",
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
            "Scores (0-100) are based on Repository stars",
        )

    def test_add_package_view(self):
        # this test has side effects, remove Package 3
        Package.objects.filter(pk=3).delete()
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
        for c in Category.objects.all():
            self.assertContains(response, c.title)
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
        with self.assertNumQueries(17):
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

    def test_add_example_view(self):
        PackageExample.objects.all().delete()
        url = reverse("add_example", kwargs={"slug": "testability"})
        with self.assertNumQueries(1):
            response = self.client.get(url)

        # The response should be a redirect, since the user is not logged in.
        self.assertEqual(response.status_code, 302)

        # Once we log in the user, we should get back the appropriate response.
        self.assertTrue(self.client.login(username="user", password="user"))
        user = User.objects.get(username="user")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "partials/sites_using_form.html")

        id_list = list(PackageExample.objects.values_list("id", flat=True))
        with self.assertNumQueries(6):
            response = self.client.post(
                url,
                {
                    "title": "TEST TITLE",
                    "url": "https://github.com",
                },
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(PackageExample.objects.count(), len(id_list) + 1)

        recently_added = PackageExample.objects.exclude(id__in=id_list).first()
        self.assertEqual(recently_added.created_by.id, user.id)

    def test_edit_example_view(self):
        user = User.objects.get(username="user")
        e = PackageExample.objects.filter(created_by=user).first()
        other_e = PackageExample.objects.exclude(created_by=user).first()

        url = reverse("edit_example", kwargs={"slug": e.package.slug, "id": e.pk})
        other_url = reverse(
            "edit_example", kwargs={"slug": other_e.package.slug, "id": other_e.pk}
        )

        # Test unauthenticated access
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

        self.assertTrue(self.client.login(username="user", password="user"))

        # Test permission denied for other user's example
        response = self.client.get(other_url)
        self.assertEqual(response.status_code, 403)

        # Test successful access for own example
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "partials/sites_using_form.html")

        # Test successful update
        response = self.client.post(
            url,
            {
                "title": "TEST TITLE",
                "url": "https://github.com",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "partials/sites_using_card.html")
        e.refresh_from_db()
        self.assertEqual(e.title, "TEST TITLE")

        # Test superuser update on other's example
        self.assertTrue(self.client.login(username="admin", password="admin"))
        response = self.client.post(
            other_url,
            {
                "title": "ADMIN EDIT",
                "url": "https://github.com",
            },
        )
        self.assertEqual(response.status_code, 200)
        other_e.refresh_from_db()
        self.assertEqual(other_e.title, "ADMIN EDIT")

    def test_delete_example_view(self):
        user = User.objects.get(username="user")
        e = PackageExample.objects.filter(created_by=user).first()
        other_e = (
            PackageExample.objects.exclude(created_by=user)
            .exclude(created_by=None)
            .first()
        )
        noone_e = PackageExample.objects.filter(created_by=None).first()

        url = reverse("delete_example", kwargs={"slug": e.package.slug, "id": e.pk})
        other_url = reverse(
            "delete_example", kwargs={"slug": other_e.package.slug, "id": other_e.pk}
        )
        noone_url = reverse(
            "delete_example", kwargs={"slug": noone_e.package.slug, "id": noone_e.pk}
        )

        # Test unauthenticated access
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)

        self.assertTrue(self.client.login(username="user", password="user"))

        # Test permission denied for other user's example
        response = self.client.get(other_url)
        self.assertEqual(response.status_code, 403)
        response = self.client.post(other_url)
        self.assertEqual(response.status_code, 403)

        # Test permission denied for example with no creator
        response = self.client.get(noone_url)
        self.assertEqual(response.status_code, 403)
        response = self.client.post(noone_url)
        self.assertEqual(response.status_code, 403)

        # Test successful access for own example
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "partials/sites_using_card.html")

        # Test successful deletion
        response = self.client.post(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "partials/sites_using_card.html")
        self.assertFalse(PackageExample.objects.filter(pk=e.pk).exists())

        # Test superuser deletion
        self.assertTrue(self.client.login(username="admin", password="admin"))
        response = self.client.post(other_url)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(PackageExample.objects.filter(pk=other_e.pk).exists())

    def test_flag_package_view(self):
        p = Package.objects.get(slug="testability")
        FlaggedPackage.objects.all().delete()
        url = reverse("flag", kwargs={"slug": p.slug})
        response = self.client.get(url)

        # The response should be a redirect, since the user is not logged in.
        self.assertEqual(response.status_code, 302)

        # Once we log in the user, we should get back the appropriate response.
        self.assertTrue(self.client.login(username="user", password="user"))
        with self.assertNumQueries(5):
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
        with self.assertNumQueries(4):
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
        with self.assertNumQueries(4):
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


class PackagePermissionTest(TestCase):
    def setUp(self):
        initial_data.load()
        for user in User.objects.all():
            profile = Profile.objects.create(user=user)
            profile.save()

        settings.RESTRICT_PACKAGE_EDITORS = True
        self.test_add_url = reverse("add_package")
        self.test_edit_url = reverse("edit_package", kwargs={"slug": "testability"})
        self.login = self.client.login(username="user", password="user")
        self.user = User.objects.get(username="user")

    def test_login(self):
        self.assertTrue(self.login)

    def test_switch_permissions(self):
        settings.RESTRICT_PACKAGE_EDITORS = False
        with self.assertNumQueries(5):
            response = self.client.get(self.test_add_url)
        self.assertEqual(response.status_code, 200)

        settings.RESTRICT_PACKAGE_EDITORS = True
        with self.assertNumQueries(6):
            response = self.client.get(self.test_add_url)
        self.assertEqual(response.status_code, 403)

    def test_add_package_permission_fail(self):
        with self.assertNumQueries(6):
            response = self.client.get(self.test_add_url)
        self.assertEqual(response.status_code, 403)

    def test_add_package_permission_success(self):
        add_package_perm = Permission.objects.get(
            codename="add_package", content_type__app_label="package"
        )
        self.user.user_permissions.add(add_package_perm)
        with self.assertNumQueries(7):
            response = self.client.get(self.test_add_url)
        self.assertEqual(response.status_code, 200)

    def test_add_package_with_grid_slug_permission_fail(self):
        grid = Grid.objects.get(slug="testing")
        url = self.test_add_url + f"?grid_slug={grid.slug}"
        with self.assertNumQueries(6):
            response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_add_package_with_grid_slug_permission_success(self):
        grid = Grid.objects.get(slug="testing")
        url = self.test_add_url + f"?grid_slug={grid.slug}"
        add_package_perm = Permission.objects.get(
            codename="add_package", content_type__app_label="package"
        )
        self.user.user_permissions.add(add_package_perm)
        with self.assertNumQueries(8):
            response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["grid"], grid)

    def test_edit_package_permission_fail(self):
        with self.assertNumQueries(6):
            response = self.client.get(self.test_edit_url)
        self.assertEqual(response.status_code, 403)

    def test_edit_package_permission_success(self):
        edit_package_perm = Permission.objects.get(
            codename="change_package", content_type__app_label="package"
        )
        self.user.user_permissions.add(edit_package_perm)
        with self.assertNumQueries(9):
            response = self.client.get(self.test_edit_url)
        self.assertEqual(response.status_code, 200)


class ValidateRepositoryURLViewTest(TestCase):
    def setUp(self):
        initial_data.load()
        for user in User.objects.all():
            Profile.objects.create(user=user)
        settings.RESTRICT_PACKAGE_EDITORS = False
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


def test_category_view(db, django_assert_num_queries, tp):
    initial_data.load()

    with django_assert_num_queries(4):
        response = tp.client.get("/categories/apps/")
    assert "apps" in str(response.content)


def test_grid_package_list(db, django_assert_num_queries, tp):
    initial_data.load()

    with django_assert_num_queries(6):
        url = tp.reverse("grid_packages", slug="testing")
        response = tp.client.get(url)

    assert response.status_code == 200


def test_package_version_list_view(db, django_assert_num_queries, tp, package_cms):
    url = tp.reverse("package_versions", slug=package_cms.slug)
    with django_assert_num_queries(2):
        response = tp.client.get(url)

    assert response.status_code == 200
    assert "partials/releases_table.html" in [t.name for t in response.templates]
