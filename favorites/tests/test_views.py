from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from package.tests import initial_data
from profiles.models import Profile
from package.models import Package


class FavoriteViewTest(TestCase):
    def setUp(self):
        initial_data.load()
        for user in User.objects.all():
            profile = Profile.objects.create(user=user)
            profile.save()

    def test_favorite_package(self):
        ID = 1
        url = reverse("add_favorite", kwargs={"id": ID})
        self.assertTrue(self.client.login(username="user", password="user"))
        package = Package.objects.get(id=ID)
        old_favorite_count = package.favorite_count
        response = self.client.post(url)
        package.refresh_from_db()
        self.assertEqual(package.favorite_count, old_favorite_count + 1)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Favorited")
        # response = self.client.post(url)
        # print(response, "reponse")
        # print(response.json, "json")
