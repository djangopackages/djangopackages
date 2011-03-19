#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
PyPI interface (see http://wiki.python.org/moin/PyPiXmlRpc)
"""

from datetime import datetime
import itertools
import xmlrpclib

from django.template.defaultfilters import slugify

from package.models import Category, Package, Version
from pypi.models import PypiUpdateLog

base_url = "http://pypi.python.org/pypi/"
PYPI = xmlrpclib.Server(base_url)

class Slurper(object):
    
    def __init__(self):
        self.package_names = PYPI.list_packages()
        self.dumb_category, created = Category.objects.get_or_create(
                                title='dummy', slug='dummy')
        self.dumb_category.save()
        
    def get_latest_version(self, package_name):
        """ Make this actually work"""
        return PYPI.package_releases(package_name)[0]
        
    def get_or_create_package(self, package_name):
        version = self.get_latest_version(package_name)
        data = PYPI.release_data(package_name, version)

        package, created = Package.objects.get_or_create(
            title           = data['name'],
            slug            = slugify(data['name']),
            category        = self.dumb_category,
            pypi_url        = base_url + data['name']
        )
        package.repo_description = data['summary'] or data['description']
        package.save()
        return package
        
    def get_or_create_all_packages(self):

        #for package_name in self.package_names:        
        for package_name in ['Django']:
            package = self.get_or_create_package(package_name)
            break