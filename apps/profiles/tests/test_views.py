from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase

from core.tests.data import create_users, STOCK_PASSWORD
from profiles.models import Profile


class TestProfile(TestCase):
    
    def setUp(self):
        super(TestProfile,self).setUp()
        create_users()
        self.user = User.objects.get(username="user")
        self.profile = Profile.objects.create(
            github_account="user",
            user=self.user,
            email=self.user.email,
        )
        
    def test_view(self):
        self.assertTrue(self.client.login(username=self.user.username, password=STOCK_PASSWORD))        
        url = reverse('profile_detail', kwargs={'github_account':self.profile.github_account})
        response = self.client.get(url)
        self.assertContains(response, "Profile for user")
        
    def test_edit(self):
        self.assertTrue(self.client.login(username=self.user.username, password=STOCK_PASSWORD))        
        
        # give me a view
        url = reverse('profile_edit')
        response = self.client.get(url)
        stuff = """<input name="email" value="user@example.com" class="textInput textinput" maxlength="75" type="text" id="id_email" />"""
        self.assertContains(response, stuff)
        
        # submit some content
        data = {
            'email':'blarg@example.com',
            }
        response = self.client.post(url, data, follow=True)
        self.assertContains(response, "Profile for user")
        p = Profile.objects.get(user=self.user)
        self.assertEquals(p.email, "blarg@example.com")
        u = User.objects.get(username=self.user.username)
        self.assertEquals(u.email, "blarg@example.com")