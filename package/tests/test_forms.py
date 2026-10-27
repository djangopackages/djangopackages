from django.test import TestCase
from package.forms import DocumentationForm, PackageCreateForm
from package.models import Category, Package


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


class DocumentationUrlTest(TestCase):
    def setUp(self):
        self.category = Category.objects.create(title="Docs", slug="docs")
        self.data = {
            "title": "Test Package",
            "slug": "test-package",
            "repo_url": "https://github.com/test/test",
            "category": self.category.pk,
        }

    def test_a_documentation_site_is_accepted(self):
        form = PackageCreateForm(
            data={**self.data, "documentation_url": "https://test.readthedocs.io/"}
        )
        self.assertTrue(form.is_valid(), form.errors)

    def test_the_repository_is_not_documentation(self):
        form = PackageCreateForm(
            data={**self.data, "documentation_url": "https://github.com/test/test/"}
        )
        self.assertFalse(form.is_valid())
        self.assertIn("already links", str(form.errors["documentation_url"]))

    def test_the_readme_and_pypi_are_not_documentation(self):
        for url in (
            "https://github.com/test/test/blob/main/README.md",
            "https://pypi.org/project/test/",
            "https://github.com/someone/else",
        ):
            with self.subTest(url=url):
                form = PackageCreateForm(data={**self.data, "documentation_url": url})
                self.assertFalse(form.is_valid())
                self.assertIn("documentation_url", form.errors)

    def test_the_sidebar_form_checks_against_the_saved_repo(self):
        package = Package.objects.create(
            title="Test Package",
            slug="test-package",
            repo_url="https://github.com/test/test",
            category=self.category,
        )
        bad = DocumentationForm(
            data={"documentation_url": "https://github.com/test/test#readme"},
            instance=package,
        )
        self.assertFalse(bad.is_valid())
        good = DocumentationForm(
            data={"documentation_url": "https://github.com/test/test/wiki"},
            instance=package,
        )
        self.assertTrue(good.is_valid(), good.errors)
        blank = DocumentationForm(data={"documentation_url": ""}, instance=package)
        self.assertTrue(blank.is_valid(), blank.errors)
