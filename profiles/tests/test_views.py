from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from core.tests.data import STOCK_PASSWORD, create_users
from favorites.models import Favorite
from package.models import Category, Package
from profiles.models import Profile


class TestProfile(TestCase):
    def setUp(self):
        super().setUp()
        create_users()
        self.user = User.objects.get(username="user")
        self.profile = Profile.objects.create(
            github_account="user",
            user=self.user,
        )
        self.category = Category.objects.create(
            title="Test Favorite",
            slug="test_favorite",
            description="Category to test favorites",
        )

    def test_view(self):
        self.assertTrue(
            self.client.login(username=self.user.username, password=STOCK_PASSWORD)
        )
        url = reverse(
            "profile_detail", kwargs={"github_account": self.profile.github_account}
        )
        response = self.client.get(url)
        self.assertContains(response, "Profile for user")

    def test_view_not_loggedin(self):
        url = reverse(
            "profile_detail", kwargs={"github_account": self.profile.github_account}
        )
        response = self.client.get(url)
        self.assertContains(response, "Profile for user")

    def test_edit_ryan(self):
        self.assertTrue(
            self.client.login(username=self.user.username, password=STOCK_PASSWORD)
        )

        # give me a view
        url = reverse("profile_edit")
        response = self.client.get(url)
        stuff = """Bitbucket account"""
        self.assertContains(response, stuff)

        # submit some content
        data = {
            "bitbucket_url": "zerg",
            "gitlab_url": "zerg",
            "extrafield_set-TOTAL_FORMS": 2,
            "extrafield_set-INITIAL_FORMS": 0,
            "extrafield_set-MIN_NUM_FORMS": 0,
            "extrafield_set-MAX_NUM_FORMS": 4,
            "extrafield-0-label": "Key1",
            "extrafield-0-url": "Value1",
            "extrafield-1-label": "Key2",
            "extrafield-1-url": "Value2",
        }
        response = self.client.post(url, data, follow=True)
        self.assertContains(response, "Profile for user")
        p = Profile.objects.get(user=self.user)
        self.assertEqual(p.bitbucket_url, "zerg")
        self.assertEqual(p.gitlab_url, "zerg")


class TestProfileContributedPackagesView(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password=STOCK_PASSWORD
        )
        self.profile = Profile.objects.create(user=self.user, github_account="testuser")
        self.url = reverse(
            "profile_contributed_packages",
            kwargs={"github_account": self.profile.github_account},
        )

    def test_view_status_code(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

    def test_view_template_used(self):
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, "new/partials/profile_packages_card.html")

    def test_htmx_view_template_used(self):
        response = self.client.get(
            self.url, headers={"hx-target": "contributed-packages-table-container"}
        )
        self.assertTemplateUsed(response, "new/partials/profile_packages_table.html")


class TestProfileFavoritePackagesView(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password=STOCK_PASSWORD
        )
        self.profile = Profile.objects.create(user=self.user, github_account="testuser")
        self.category = Category.objects.create(title="Test", slug="test")
        self.package = Package.objects.create(
            title="Test Package", slug="test-package", category=self.category
        )
        Favorite.objects.create(favorited_by=self.user, package=self.package)
        self.url = reverse(
            "profile_favorite_packages",
            kwargs={"github_account": self.profile.github_account},
        )

    def test_view_status_code_owner(self):
        self.client.login(username="testuser", password=STOCK_PASSWORD)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Package")

    def test_view_status_code_other_user_private(self):
        User.objects.create_user(username="other", password=STOCK_PASSWORD)
        self.client.login(username="other", password=STOCK_PASSWORD)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    def test_view_status_code_other_user_public(self):
        self.profile.share_favorites = True
        self.profile.save()
        User.objects.create_user(username="other", password=STOCK_PASSWORD)
        self.client.login(username="other", password=STOCK_PASSWORD)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Package")

    def test_view_template_used(self):
        self.client.login(username="testuser", password=STOCK_PASSWORD)
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, "new/partials/profile_packages_card.html")

    def test_htmx_view_template_used(self):
        self.client.login(username="testuser", password=STOCK_PASSWORD)
        response = self.client.get(
            self.url, headers={"hx-target": "favorite-packages-table-container"}
        )
        self.assertTemplateUsed(response, "new/partials/profile_packages_table.html")
