import pytest

from django.utils.timezone import now
from model_bakery import baker, seq

from package.models import Category, Package


@pytest.fixture(scope="function")
def search_fixtures(django_db_blocker, django_user_model):
    with django_db_blocker.unblock():
        user = baker.make(django_user_model)
        category = baker.make(Category)
        package = baker.make(
            Package,
            category=category,
            repo_url=seq("https://github.com/djangopackages/djangopackages"),
            slug=seq("django-packages"),
            supports_python3=True,
            title="Django Packages",
        )
        baker.make(
            Package,
            category=category,
            date_repo_archived=now(),
            repo_url="https://github.com/djangopackages/archived",
            slug="archived",
            supports_python3=True,
            title="Archived",
        )
        baker.make(
            Package,
            category=category,
            date_deprecated=now(),
            repo_url="https://github.com/djangopackages/deprecated-by-date",
            slug="deprecated-by-date",
            supports_python3=True,
            title="Deprecated by Date",
        )
        baker.make(
            Package,
            category=category,
            deprecated_by=user,
            repo_url="https://github.com/djangopackages/deprecated-by-user",
            slug="deprecated-by-user",
            supports_python3=True,
            title="Deprecated by User",
        )
        baker.make(
            Package,
            category=category,
            deprecates_package=package,
            repo_url="https://github.com/djangopackages/deprecates-package",
            slug="deprecates-package",
            supports_python3=True,
            title="Deprecated by Package",
        )
        baker.make(
            Package,
            category=category,
            repo_url="https://github.com/djangopackages/python2",
            slug="python2",
            supports_python3=False,
            title="Python2 only",
        )
        baker.make(
            Package,
            category=category,
            repo_url="https://github.com/bigskysoftware/htmx",
            slug="htmx",
            title="HTMX",
        )


def test_managers(db, search_fixtures):
    assert Package.objects.all().count() == 7
    assert Package.objects.active().count() == 3
    assert Package.objects.archived().count() == 1
    assert Package.objects.deprecated().count() == 3
    assert Package.objects.supports_python3().count() == 5


def test_archived_managers(db, category, search_fixtures):
    all_packages = Package.objects.all().count()
    active_packages = Package.objects.active().count()
    archived_packages = Package.objects.archived().count()

    baker.make(
        Package,
        category=category,
        date_repo_archived=now(),
        repo_url=seq("https://github.com/djangopackages/archived-"),
        _quantity=10,
    )

    assert all_packages < Package.objects.all().count()
    assert active_packages == Package.objects.active().count()
    assert archived_packages < Package.objects.archived().count()


def test_deprecated_managers(db, category, package, search_fixtures):
    all_packages = Package.objects.all().count()
    active_packages = Package.objects.active().count()
    deprecated_packages = Package.objects.deprecated().count()

    baker.make(
        Package,
        category=category,
        date_deprecated=now(),
        deprecates_package=package,
        repo_url=seq("https://github.com/djangopackages/archived-"),
    )

    assert all_packages < Package.objects.all().count()
    assert active_packages == Package.objects.active().count()
    assert deprecated_packages < Package.objects.deprecated().count()


def test_supports_python3_managers(db, search_fixtures):
    all_packages = Package.objects.all().count()
    active_packages = Package.objects.active().count()
    supports_python3_packages = Package.objects.supports_python3().count()

    baker.make(
        Package,
        repo_url="https://github.com/djangopackages/supports-python3-",
    )
    baker.make(
        Package,
        repo_url="https://github.com/djangopackages/supports-python3-true",
        supports_python3=True,
    )
    baker.make(
        Package,
        repo_url="https://github.com/djangopackages/supports-python3-false",
        supports_python3=False,
    )

    assert Package.objects.all().count() == all_packages + 3
    assert Package.objects.active().count() == active_packages + 3
    assert Package.objects.supports_python3().count() > supports_python3_packages
