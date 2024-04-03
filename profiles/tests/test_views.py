from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from core.tests.data import STOCK_PASSWORD, create_users
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
            "extrafields_set-TOTAL_FORMS": 2,
            "extrafields_set-INITIAL_FORMS": 0,
            "extrafields_set-MIN_NUM_FORMS": 0,
            "extrafields_set-MAX_NUM_FORMS": 4,
            "extrafields-0-key": "Key1",
            "extrafields-0-value": "Value1",
            "extrafields-1-key": "Key2",
            "extrafields-1-value": "Value2",
        }
        response = self.client.post(url, data, follow=True)
        self.assertContains(response, "Profile for user")
        p = Profile.objects.get(user=self.user)
        self.assertEqual(p.bitbucket_url, "zerg")
        self.assertEqual(p.gitlab_url, "zerg")
