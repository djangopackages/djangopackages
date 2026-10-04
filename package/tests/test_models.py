from django.contrib.auth.models import User
from django.test import TestCase

from package.forms import PackageCreateForm
from package.models import FlaggedPackage, Package
from package.repos.forgejo import ForgejoHandler
from package.tests import initial_data


def test_version_order(package_cms):
    versions = package_cms.version_set.by_version()
    expected_values = [
        "2.0.0",
        "2.0.1",
        "2.0.2",
        "2.1.0",
        # "2.1.0.beta3",
        # "2.1.0.rc1",
        # "2.1.0.rc2",
        # "2.1.0.rc3",
        "2.1.1",
        "2.1.2",
        "2.1.3",
    ]
    assert [v.number for v in versions] == expected_values


def test_version_license_length(version):
    version.license = "x" * 50
    version.save()
    assert version.license == "Custom"


class PackageTests(TestCase):
    def setUp(self):
        initial_data.load()

    def test_pypi_name_blank(self):
        package = Package.objects.get(slug="serious-testing")
        self.assertEqual(package.pypi_url, "")
        self.assertEqual(package.pypi_name, "")

    def test_pypi_name_valid(self):
        package = Package.objects.get(slug="supertester")
        self.assertEqual(package.pypi_url, "django-crispy-forms")
        self.assertEqual(package.pypi_name, "django-crispy-forms")
        self.assertEqual(
            package.get_pypi_uri(), "https://pypi.org/project/django-crispy-forms/"
        )
        self.assertEqual(
            package.get_pypi_json_uri(),
            "https://pypi.org/pypi/django-crispy-forms/json",
        )

    def test_pypi_name_invalid(self):
        package = Package.objects.get(slug="testability")
        self.assertEqual(
            package.pypi_url, "https://pypi.org/project/django-la-facebook/"
        )
        self.assertEqual(package.pypi_name, "django-la-facebook")

        package.pypi_url = ""
        self.assertEqual(package.pypi_name, "")

        package.pypi_url = "http://pypi.python.org/pypi/django-la-facebook/"
        self.assertEqual(package.pypi_name, "django-la-facebook")
        self.assertEqual(
            package.get_pypi_uri(), "https://pypi.org/project/django-la-facebook/"
        )
        self.assertEqual(
            package.get_pypi_json_uri(), "https://pypi.org/pypi/django-la-facebook/json"
        )

        package.pypi_url = "https://pypi.python.org/pypi/django-la-facebook/"
        self.assertEqual(package.pypi_name, "django-la-facebook")

    def test_pypi_license(self):
        for p in Package.objects.all():
            self.assertIsNone(p.pypi_license)

    def test_pypi_license_display(self):
        for p in Package.objects.all():
            self.assertEqual(p.pypi_license_display, "UNKNOWN")

    def test_package_form(self):
        f = PackageCreateForm()
        assert 'placeholder="ex: https://github.com/django/django"' in str(f)

    def test_package_flag(self):
        p = Package.objects.get(slug="testability")
        f = FlaggedPackage.objects.create(
            package=p,
            reason="This is a test",
            user=User.objects.get(username="user"),
        )

        f.approve()
        self.assertEqual(f.approved_flag, True)

        expected_string = f"{p.repo_name} - {f.reason}"
        self.assertEqual(str(f), expected_string)


def test_package_repo_uses_repo_host(package_forgejo):
    assert isinstance(package_forgejo.repo, ForgejoHandler)


def test_package_repo_name_strips_git_suffix(package_forgejo):
    package_forgejo.repo_url = "https://git.example.com/example/forgejo-repo.git"
    assert package_forgejo.repo_name() == "example/forgejo-repo"
