from django.contrib.auth.models import User
from django.db import models

from core.models import BaseModel
from package.models import Package

base_url = "http://pypi.python.org/pypi/"

def get_package_by_pypi_name(self, pypi_name):
    if base_url not in pypi_name:
        url = "http://pypi.python.org/pypi/%s" + pypi_name
    return self.get_query_set().get(pypi_url=base_url)


class PackageStaff(object):
    """ This represents the management of the canonical source. 
        Can be implemented for other things besides Python. Say gems or whacks
        This through table is isolated to make the coupling with Package.package very loose.
        # TODO - make this a third party package
    """
    
    package = models.ForeignKey(Package)    
    user = models.ForeignKey(User, related_name="package_staff")