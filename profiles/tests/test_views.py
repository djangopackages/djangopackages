from __future__ import unicode_literals
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase

from core.tests.data import create_users, STOCK_PASSWORD
from profiles.models import Profile


class TestProfile(TestCase):

    def setUp(self):
        super(TestProfile, self).setUp()
        create_users()
        self.user = User.objects.get(username="user")
        self.profile = Profile.objects.create(
            github_account="user",
            user=self.user,
        )

    def test_view(self):
        self.assertTrue(self.client.login(username=self.user.username, password=STOCK_PASSWORD))
        url = reverse('profile_detail', kwargs={'github_account': self.profile.github_account})
        response = self.client.get(url)
        self.assertContains(response, "Profile for user")

    def test_view_not_loggedin(self):
        url = reverse('profile_detail', kwargs={'github_account': self.profile.github_account})
        response = self.client.get(url)
        self.assertContains(response, "Profile for user")

    def test_edit(self):
        self.assertTrue(self.client.login(username=self.user.username, password=STOCK_PASSWORD))

        # give me a view
        url = reverse('profile_edit')
        response = self.client.get(url)
        stuff = """<input id="id_bitbucket_url" type="text" class="textInput textinput" name="bitbucket_url" maxlength="100" />"""
        stuff = """<input id="id_bitbucket_url" type="text" class="textinput textInput form-control" name="bitbucket_url" maxlength="100" />"""
        self.assertContains(response, stuff)

        # submit some content
        data = {
            'bitbucket_url': 'zerg',
            }
        response = self.client.post(url, data, follow=True)
        self.assertContains(response, "Profile for user")
        p = Profile.objects.get(user=self.user)
        self.assertEquals(p.bitbucket_url, "zerg")
