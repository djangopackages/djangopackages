import pytest

from django.test import TestCase

from package.models import Package, Category


class TestGitlabRepo(TestCase):
    def setUp(self):
        self.category = Category.objects.create(title="dummy", slug="dummy")
        self.category.save()
        self.package = Package.objects.create(
            title="Django",
            slug="django",
            repo_url="https://gitlab.com/delta10/kees",
            category=self.category,
        )
