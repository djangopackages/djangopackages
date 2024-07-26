from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from package.tests import initial_data
from profiles.models import Profile
from package.models import Package
from favorites.models import Favorite


class FavoriteViewTest(TestCase):
    def setUp(self):
        initial_data.load()
        for user in User.objects.all():
            profile = Profile.objects.create(user=user)
            profile.save()
        self.package_id = 1
        self.user = User.objects.get(username="user")
        self.login = self.client.login(username="user", password="user")

    def test_favorite_package(self):
        url = reverse("add_favorite", kwargs={"id": self.package_id})
        package = Package.objects.get(id=self.package_id)
        old_favorite_count = package.favorite_count
        response = self.client.post(url)
        package.refresh_from_db()
        self.assertEqual(package.favorite_count, old_favorite_count + 1)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Favorited")

    def test_unfavorite_package(self):
        package = Package.objects.get(id=self.package_id)
        Favorite.objects.create(favorited_by=self.user, package=package)
        package.refresh_from_db()
        old_favorite_count = package.favorite_count
        url = reverse("remove_favorite", kwargs={"id": self.package_id})
        response = self.client.post(url)
        package.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(package.favorite_count, old_favorite_count - 1)
        self.assertContains(response, "Add to Favorite")
