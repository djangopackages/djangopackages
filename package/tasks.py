from django.shortcuts import get_object_or_404
from django.utils import timezone

from package.models import Package
from package.pypi import update_package_from_pypi
from package.scores import update_package_score


def fetch_package_data_task(slug):
    package = get_object_or_404(Package, slug=slug)
    update_package_from_pypi(package, save=False)
    package.repo.fetch_metadata(package, save=False)
    update_package_score(package, save=False)
    package.last_fetched = timezone.now()
    package.save()


def import_from_pypi_task(name: str, category_slug: str = "apps") -> str:
    """Create one package from its PyPI name and fill it in.

    Queued by `pypi_import --queue`. Not scheduled anywhere, on purpose:
    nothing filters spam or malware out of the discovery feed yet, so a
    person reviews the list before this runs (#1810).
    """
    from package.importer import import_from_pypi
    from package.models import Category

    category = Category.objects.get(slug=category_slug)
    result = import_from_pypi(name, category=category)
    return f"{result.name}: {result.status} {result.note}".strip()
