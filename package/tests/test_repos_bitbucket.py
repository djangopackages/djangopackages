import pytest

from django.test import TestCase

from package.repos.bitbucket import BitbucketHandler
from package.models import Package, Category, Commit


class TestBitbucketRepo(TestCase):
    def setUp(self):
        self.category = Category.objects.create(title="dummy", slug="dummy")
        self.category.save()
        self.package = Package.objects.create(
            category=self.category,
            title="django-mssql",
            slug="django-mssql",
            repo_url="https://bitbucket.org/Manfre/django-mssql/",
        )
        self.bitbucket_handler = BitbucketHandler()

    def test_fetch_commits(self):
        self.assertEqual(Commit.objects.count(), 0)
        self.bitbucket_handler.fetch_commits(self.package)
        self.assertNotEqual(Commit.objects.count(), 0)

    def test_fetch_metadata(self):
        package = self.bitbucket_handler.fetch_metadata(self.package)
        self.assertTrue(
            package.repo_description.startswith(
                "Microsoft SQL server backend for Django running on windows"
            )
        )
        self.assertTrue(package.repo_watchers > 0)
        self.assertTrue(package.repo_forks > 0)
        self.assertEqual(package.participants, "Manfre")
