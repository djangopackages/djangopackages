from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from grid.models import Grid, GridPackage
from package.models import Package, Category
from profiles.models import Profile


class BaseData(TestCase):
    def setUp(self):
        """
        Set up initial data, done through Python because fixtures break way too
        quickly with migrations and are terribly hard to maintain.
        """
        self.now = timezone.now()
        self.app = Category.objects.create(
            title='App',
            slug='app',
        )
        self.framework = Category.objects.create(
            title='Framework',
            slug='framework',
        )
        self.grid = Grid.objects.create(
            title='A Grid',
            slug='grid',
        )
        self.pkg1 = Package.objects.create(
            title='Package1',
            slug='package1',
            category=self.app,
            repo_url='https://github.com/pydanny/django-uni-form',
            last_fetched=self.now
        )
        self.pkg2 = Package.objects.create(
            title='Package2',
            slug='package2',
            category=self.app,
            repo_url='https://github.com/cartwheelweb/opencomparison'
        )
        GridPackage.objects.create(package=self.pkg1, grid=self.grid)
        GridPackage.objects.create(package=self.pkg2, grid=self.grid)
        self.user = User.objects.create_user('user', 'user@opencomparison.com', 'user')
        self.profile = Profile.objects.create(
            user=self.user,
            github_account="user"
        )

        self.pkg1.usage.add(self.user)

        self.pkg3 = Package.objects.create(
            title='Package3',
            slug='package3',
            category=self.framework,
            repo_url='https://github.com/divio/django-cms',
            created_by=self.user
        )