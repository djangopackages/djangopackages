from celery.decorators import task

from package.models import Package

@task
def fetch_package_metadata(pk):
    package = Package.objects.get(pk=pk)
    package.fetch_metadata()
    print "Updated %s's metadata" % package.slug

@task
def queue_package_updates(package_limit=None):
    all_packages = Package.objects.all().values_list('id', flat=True)[:package_limit]

    # If this is actually a performance issue, make it a map
    for package in all_packages:
        print "Queued id: %s for updating" % package
        fetch_package_metadata.delay(package)