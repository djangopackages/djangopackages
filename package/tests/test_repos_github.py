import pytest

from django.test import TestCase

from package.repos.github import GitHubHandler
from package.models import Package, Category, Commit


class TestGithubRepo(TestCase):
    def setUp(self):
        self.category = Category.objects.create(title="dummy", slug="dummy")
        self.category.save()
        self.package = Package.objects.create(
            title="Django Enhancement Proposals",
            slug="deps",
            repo_url="https://github.com/django/deps",
            category=self.category,
        )
        self.github_handler = GitHubHandler()
        self.archived_package = Package.objects.create(
            title="dj-paginator",
            slug="dj-paginator",
            repo_url="https://github.com/pydanny/dj-paginator",
            category=self.category,
        )
        self.invalid_package = Package.objects.create(
            title="Invalid Package",
            slug="invldpkg",
            repo_url="https://example.com",
            category=self.category,
        )

    def test_fetch_commits(self):
        self.assertEqual(Commit.objects.count(), 0)
        self.github_handler.fetch_commits(self.package)
        self.assertTrue(Commit.objects.count() > 0)

    def test_fetch_metadata(self):
        # Currently a live tests that access github
        package = self.github_handler.fetch_metadata(self.package)
        self.assertEqual(
            package.repo_description,
            "Django Enhancement Proposals",
        )
        self.assertTrue(package.repo_watchers > 100)

    def test_fetch_metadata_archived_repo(self):
        # test what happens when we reference an archived repository
        assert self.archived_package.date_repo_archived is None
        package = self.github_handler.fetch_metadata(self.archived_package)

        assert self.archived_package.date_repo_archived is not None
        assert package.repo_description == "Django + Pagination made easy."
        assert package.date_repo_archived is not None

    def test_fetch_metadata_unsupported_repo(self):
        # test what happens when setting up an unsupported repository
        self.package.repo_url = "https://example.com"
        package = self.github_handler.fetch_metadata(self.invalid_package)

        self.assertEqual(package.repo_description, "")
        self.assertEqual(package.repo_watchers, 0)
        self.invalid_package.fetch_commits()
        self.assertEqual(package.commit_set.count(), 0)
