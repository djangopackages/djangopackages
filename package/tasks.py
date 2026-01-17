from django.shortcuts import get_object_or_404
from django.utils import timezone

from package.models import Package
from package.pypi import update_package_from_pypi


def fetch_package_data_task(slug):
    package = get_object_or_404(Package, slug=slug)
    package = update_package_from_pypi(package, save=False)
    package.repo.fetch_metadata(package, save=False)
    package.repo.fetch_commits(package, save=False)
    package.last_fetched = timezone.now()
    package.save()
