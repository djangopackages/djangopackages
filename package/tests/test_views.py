from textwrap import dedent

import pytest
from django.conf import settings
from django.contrib.auth.models import Permission, User
from django.contrib.humanize.templatetags.humanize import intcomma
from django.test import TestCase
from django.urls import reverse
from waffle.testutils import override_flag

from package.models import Category, FlaggedPackage, Package, PackageExample
from package.tests import initial_data
from profiles.models import Profile


def test_python3_list(db, django_assert_num_queries, tp):
    # TODO: refactor initial_data to be a fixture that's only loaded once
    initial_data.load()

    assert Package.objects.count() == 4

    url = tp.reverse("py3_compat")
    with django_assert_num_queries(5):
        response = tp.client.get(url)

    assert response.status_code == 200


def test_python3_list_blank_sort_empty(db, django_assert_num_queries, tp):
    # TODO: refactor initial_data to be a fixture that's only loaded once
    initial_data.load()

    assert Package.objects.count() == 4

    url = tp.reverse("py3_compat")
    with django_assert_num_queries(5):
        response = tp.client.get(url, data={"dir": ""})
    assert response.status_code == 200


def test_python3_list_blank_sort_asc(db, django_assert_num_queries, tp):
    # TODO: refactor initial_data to be a fixture that's only loaded once
    initial_data.load()

    assert Package.objects.count() == 4

    url = tp.reverse("py3_compat")
    with django_assert_num_queries(5):
        response = tp.client.get(url, data={"dir": "asc"})
    assert response.status_code == 200


def test_python3_list_blank_sort_desc(db, django_assert_num_queries, tp):
    # TODO: refactor initial_data to be a fixture that's only loaded once
    initial_data.load()

    assert Package.objects.count() == 4

    url = tp.reverse("py3_compat")
    with django_assert_num_queries(5):
        response = tp.client.get(url, data={"dir": "desc"})
    assert response.status_code == 200


def test_python3_list_blank_sort_by_valid_field(db, django_assert_num_queries, tp):
    # TODO: refactor initial_data to be a fixture that's only loaded once
    initial_data.load()

    assert Package.objects.count() == 4

    url = tp.reverse("py3_compat")
    with django_assert_num_queries(5):
        response = tp.client.get(url, data={"dir": "desc", "sort": "repo_watchers"})
    assert response.status_code == 200


def test_python3_list_blank_sort_by_bad_field(db, django_assert_num_queries, tp):
    # TODO: refactor initial_data to be a fixture that's only loaded once
    initial_data.load()

    assert Package.objects.count() == 4

    url = tp.reverse("py3_compat")
    with django_assert_num_queries(5):
        response = tp.client.get(url, data={"dir": "desc", "sort": "doesnotexist"})
    assert response.status_code == 200


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
        with self.assertNumQueries(15):
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
        self.assertTemplateUsed(response, "package/package.html")
        package = Package.objects.get(slug="testability")
        self.assertContains(
            response,
            dedent("""
                <th
                    data-testid="repository-statistics-score-header"
                    scope="col"
                    aria-label="Score"
                    data-toggle="tooltip"
                    data-placement="top"
                    title="Scores (0-100) are based on Repository stars, with deductions for inactivity (-10% every 3 months) and lack of Python 3 support (-30%)."
                >
                    <span class="glyphicon glyphicon-stats"></span>
                </th>
            """),
            html=True,
        )
        self.assertContains(
            response,
            dedent(f"""
                <td data-testid="repository-statistics-score-cell">
                    {intcomma(package.score)}
                </td>
            """),
            html=True,
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
        self.assertTemplateUsed(response, "package/package.html")
        self.assertNotContains(
            response,
            'data-testid="repository-statistics-score-header"',
        )
        self.assertNotContains(
            response,
            'data-testid="repository-statistics-score-cell"',
        )

    def test_latest_packages_view(self):
        url = reverse("latest_packages")
        with self.assertNumQueries(6):
            response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "package/package_archive.html")
        packages = Package.objects.all()
        for p in packages:
            self.assertContains(response, p.title)
            self.assertContains(response, p.repo_description)

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
        self.assertTemplateUsed(response, "package/package_form.html")
        for c in Category.objects.all():
            self.assertContains(response, c.title)
        count = Package.objects.count()
        with self.assertNumQueries(14):
            response = self.client.post(
                url,
                {
                    "category": Category.objects.first().pk,
                    "repo_url": "https://github.com/django/django",
                    "slug": "django",
                    "title": "django",
                },
            )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Package.objects.count(), count + 1)

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
        self.assertTemplateUsed(response, "package/package_form.html")
        self.assertContains(response, p.title)
        self.assertContains(response, p.slug)

        # Make a test post
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
        with self.assertNumQueries(0):
            response = self.client.get(url)

        # The response should be a redirect, since the user is not logged in.
        self.assertEqual(response.status_code, 302)

        # Once we log in the user, we should get back the appropriate response.
        self.assertTrue(self.client.login(username="user", password="user"))
        user = User.objects.get(username="user")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "package/add_example.html")

        id_list = list(PackageExample.objects.values_list("id", flat=True))
        with self.assertNumQueries(4):
            response = self.client.post(
                url,
                {
                    "title": "TEST TITLE",
                    "url": "https://github.com",
                },
            )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(PackageExample.objects.count(), len(id_list) + 1)

        recently_added = PackageExample.objects.exclude(id__in=id_list).first()
        self.assertEqual(recently_added.created_by.id, user.id)

    def test_edit_example_view(self):
        user = User.objects.get(username="user")
        e = PackageExample.objects.exclude(created_by=user).first()
        id = e.pk
        url = reverse("edit_example", kwargs={"slug": e.package.slug, "id": e.pk})
        with self.assertNumQueries(0):
            response = self.client.get(url)

        # The response should be a redirect, since the user is not logged in.
        self.assertEqual(response.status_code, 302)

        # Once we log in the user, we should get back the appropriate response.
        self.assertTrue(self.client.login(username="user", password="user"))
        with self.assertNumQueries(8):
            response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "package/edit_example.html")
        self.assertNotContains(response, "example-delete-btn")

        with self.assertNumQueries(5):
            response = self.client.post(
                url,
                {
                    "title": "TEST TITLE",
                    "url": "https://github.com",
                },
            )
        self.assertEqual(response.status_code, 302)
        e = PackageExample.objects.get(pk=id)
        self.assertEqual(e.title, "TEST TITLE")

        deletable_e = PackageExample.objects.filter(created_by=user).first()
        url = reverse(
            "edit_example", kwargs={"slug": e.package.slug, "id": deletable_e.pk}
        )
        with self.assertNumQueries(8):
            response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "example-delete-btn")

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

        with self.assertNumQueries(0):
            response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

        self.assertTrue(self.client.login(username="user", password="user"))

        with self.assertNumQueries(4):
            response = self.client.get(other_url)
        self.assertEqual(response.status_code, 403)

        with self.assertNumQueries(3):
            response = self.client.get(noone_url)
        self.assertEqual(response.status_code, 403)

        with self.assertNumQueries(8):
            response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        confirm_url = reverse(
            "confirm_delete_example", kwargs={"slug": e.package.slug, "id": e.pk}
        )
        confirm_other_url = reverse(
            "confirm_delete_example",
            kwargs={"slug": other_e.package.slug, "id": other_e.pk},
        )
        confirm_noone_url = reverse(
            "delete_example", kwargs={"slug": noone_e.package.slug, "id": noone_e.pk}
        )

        response = self.client.post(confirm_other_url)
        self.assertEqual(response.status_code, 403)
        response = self.client.post(confirm_noone_url)
        self.assertEqual(response.status_code, 403)

        response = self.client.post(confirm_url)
        self.assertEqual(response.status_code, 302)
        self.assertRaises(
            PackageExample.DoesNotExist, PackageExample.objects.get, id=e.id
        )

    def test_flag_package_view(self):
        p = Package.objects.get(slug="testability")
        FlaggedPackage.objects.all().delete()
        url = reverse("flag", kwargs={"slug": p.slug})
        response = self.client.get(url)

        # The response should be a redirect, since the user is not logged in.
        self.assertEqual(response.status_code, 302)

        # Once we log in the user, we should get back the appropriate response.
        self.assertTrue(self.client.login(username="user", password="user"))
        with self.assertNumQueries(6):
            response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "package/flag_form.html")

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
        url = reverse("flag_approve", kwargs={"slug": f.package.slug})
        with self.assertNumQueries(7):
            response = self.client.get(url)

        # The response should be a redirect, since the user is not logged in.
        self.assertEqual(response.status_code, 302)

        # Once we log in the user, we should get back the appropriate response.
        self.assertTrue(self.client.login(username="user", password="user"))
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
        url = reverse("flag_remove", kwargs={"slug": f.package.slug})
        with self.assertNumQueries(7):
            response = self.client.get(url)

        # The response should be a redirect, since the user is not logged in.
        self.assertEqual(response.status_code, 302)

        # Once we log in the user, we should get back the appropriate response.
        self.assertTrue(self.client.login(username="user", password="user"))
        with self.assertNumQueries(9):
            response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

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
        with self.assertNumQueries(9):
            response = self.client.get(url)
        self.assertEqual(count + 1, user.package_set.count())

        # Now we remove that same package from the user's list of used packages,
        # making sure that the total number has decreased by one.
        url = reverse("usage", kwargs={"slug": "testability", "action": "remove"})
        with self.assertNumQueries(8):
            response = self.client.get(url)
        self.assertEqual(count, user.package_set.count())


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
        with self.assertNumQueries(7):
            response = self.client.get(self.test_add_url)
        self.assertEqual(response.status_code, 200)

        settings.RESTRICT_PACKAGE_EDITORS = True
        with self.assertNumQueries(5):
            response = self.client.get(self.test_add_url)
        self.assertEqual(response.status_code, 403)

    def test_add_package_permission_fail(self):
        with self.assertNumQueries(5):
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

    def test_edit_package_permission_fail(self):
        with self.assertNumQueries(5):
            response = self.client.get(self.test_edit_url)
        self.assertEqual(response.status_code, 403)

    def test_edit_package_permission_success(self):
        edit_package_perm = Permission.objects.get(
            codename="change_package", content_type__app_label="package"
        )
        self.user.user_permissions.add(edit_package_perm)
        with self.assertNumQueries(10):
            response = self.client.get(self.test_edit_url)
        self.assertEqual(response.status_code, 200)


def test_category_view(db, django_assert_num_queries, tp):
    initial_data.load()

    with django_assert_num_queries(23):
        response = tp.client.get("/categories/apps/")
    assert "apps" in str(response.content)


def test_grid_package_list(db, django_assert_num_queries, tp):
    initial_data.load()

    with django_assert_num_queries(19):
        url = tp.reverse("grid_packages", slug="testing")
        response = tp.client.get(url)

    assert response.status_code == 200
