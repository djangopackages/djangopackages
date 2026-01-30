from django.test import TestCase
from package.forms import PackageCreateForm
from package.models import Category


class PackageFormTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(
            title="Test Category", slug="test-category"
        )

    def test_clean_pypi_url_with_full_url(self):
        form_data = {
            "title": "Test Package",
            "slug": "test-package",
            "repo_url": "https://github.com/test/test",
            "category": self.category.pk,
            "pypi_url": "https://pypi.org/project/test-package/",
        }
        form = PackageCreateForm(data=form_data)
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(
            form.cleaned_data["pypi_url"], "https://pypi.org/project/test-package/"
        )

    def test_clean_pypi_url_with_package_name_only(self):
        form_data = {
            "title": "Test Package 2",
            "slug": "test-package-2",
            "repo_url": "https://github.com/test/test2",
            "category": self.category.pk,
            "pypi_url": "test-package-2",
        }
        form = PackageCreateForm(data=form_data)
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(
            form.cleaned_data["pypi_url"], "https://pypi.org/project/test-package-2/"
        )

    def test_clean_pypi_url_empty(self):
        form_data = {
            "title": "Test Package 3",
            "slug": "test-package-3",
            "repo_url": "https://github.com/test/test3",
            "category": self.category.pk,
            "pypi_url": "",
        }
        form = PackageCreateForm(data=form_data)
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(form.cleaned_data["pypi_url"], "")

    def test_clean_pypi_url_with_http_prefix(self):
        form_data = {
            "title": "Test Package 3",
            "slug": "test-package-3",
            "repo_url": "https://github.com/test/test3",
            "category": self.category.pk,
            "pypi_url": "http-package-name",
        }
        form = PackageCreateForm(data=form_data)
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(
            form.cleaned_data["pypi_url"], "https://pypi.org/project/http-package-name/"
        )
