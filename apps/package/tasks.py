from celery.decorators import task

from packaginator.apps.package.models import Package


@task()
def fetch_package_metadata(pk):
    package = Package.objects.get(pk=pk)
    package.fetch_metadata()
