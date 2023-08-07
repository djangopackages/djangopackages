from django.shortcuts import get_object_or_404
from django.utils import timezone

from package.models import Package


def fetch_package_data_task(slug):
    package = get_object_or_404(Package, slug=slug)
    package.fetch_pypi_data()
    package.repo.fetch_metadata(package)
    package.repo.fetch_commits(package)
    package.last_fetched = timezone.now()
    package.save()
