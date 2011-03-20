from celery.decorators import task

from package.models import Package
from pypi.slurper import Slurper
base_url = "http://pypi.python.org/pypi/"
import xmlrpclib
PYPI = xmlrpclib.Server(base_url)



@task()
def get_package_pypi(package_name):
    s = Slurper(package=package_name)
    versions = PYPI.package_releases(package_name)
    highest_version = s.get_latest_version_number(package_name, versions)
    package = s.get_or_create_package(package_name, highest_version)            
    print package
    for version in versions:
        if version == highest_version:
            continue
        print version
