from celery.task import task
from pypi.slurper import Slurper

import xmlrpclib
base_url = "http://pypi.python.org/pypi/"
PYPI = xmlrpclib.Server(base_url)

@task()
def get_package_from_pypi(package_name):
    s = Slurper(package=package_name)
    versions = PYPI.package_releases(package_name)
    highest_version = s.get_latest_version_number(package_name, versions)
    package, created = s.get_or_create_package(package_name, highest_version)
    if created:
        print "Created %s" % package.slug
    else:
        print "%s Already Exists" % package.slug

@task
def queue_all_pypi_packages(package_limit=None):
    """
    Puts all of Pypi into the celery queue
    """

    package_names = PYPI.list_packages()
    for i, package_name in enumerate(package_names):
        if package_limit and i > package_limit:
            break
        try:
            get_package_from_pypi.delay(package_name)
            print "Queued %s to slurp from PyPi" % package_name
        except UnicodeDecodeError, UnicodeError:
            print "Couldn't queue %s due to Unicode Error" % package_name
