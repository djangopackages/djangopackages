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

    def test_view_with_favorite_packages(self):
        self.profile.share_favorites = True
        self.profile.save()
        package = Package.objects.create(
            title="Test Favorite", slug="test_favorite", category=self.category
        )
        Favorite.objects.create(package=package, favorited_by=self.user)
        self.assertTrue(
            self.client.login(username=self.user.username, password=STOCK_PASSWORD)
        )
        url = reverse(
            "profile_detail", kwargs={"github_account": self.profile.github_account}
        )
        response = self.client.get(url)
        self.assertContains(response, "Profile for user")
        self.assertContains(response, "Favorite packages")
        self.assertContains(response, "Test Favorite")

    def test_view_without_favorite_packages(self):
        self.profile.share_favorites = False
        self.profile.save()
        package = Package.objects.create(
            title="Test Favorite 2", slug="test_favorite_2", category=self.category
        )
        Favorite.objects.create(package=package, favorited_by=self.user)
        self.assertTrue(
            self.client.login(username=self.user.username, password=STOCK_PASSWORD)
        )
        url = reverse(
            "profile_detail", kwargs={"github_account": self.profile.github_account}
        )
        response = self.client.get(url)
        self.assertContains(response, "Profile for user")
        self.assertNotContains(response, "Favorite packages")
