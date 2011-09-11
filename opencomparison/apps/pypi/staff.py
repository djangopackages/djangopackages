#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
PyPI interface (see http://wiki.python.org/moin/PyPiXmlRpc)
"""

import xmlrpclib

from django.contrib.auth.models import User

from celery.decorators import task

from package.models import Package
from pypi.models import PackageStaff, get_package_by_pypi_name
from pypi.slurper import Slurper

base_url = "http://pypi.python.org/pypi/"
PYPI = xmlrpclib.Server(base_url)


def get_package_name(package):
    if isinstance(package, Package):
        return package.pypi_name
    return package    

def get_package_staff(package):
    """ Get the staff associated to a given package name """
    package_name = get_package_name(package)
    return [x[1] for x in PYPI.package_roles(package_name)]
    
def build_staff_for_package(package):
    """ TODO check for people no longer staff of a package """
    package_name = get_package_name(package)
    package = get_package_by_pypi_name(package_name)
    for staff_name in get_package_staff(package_name):
        try:
            user = User.objects.get(username=staff_name)
        except User.DoesNotExist:
            # User not in system yet so we skip them
            continue
        
        package_staff = PackageStaff.objects.get_or_create(
            user=user,
            package=package
        )
        package_staff.save()
        
    

def get_user_packages(username):
    """ roles and packages associated to a given user name """
    return [x[1] for x in PYPI.user_packages(username)]


def build_packages_for_staff(username):
    pass
    
