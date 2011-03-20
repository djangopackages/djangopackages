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
from package.repos import get_repo_for_repo_url
from pypi.models import PypiUpdateLog
from pypi.versioning import highest_version

from celery.decorators import task

base_url = "http://pypi.python.org/pypi/"
PYPI = xmlrpclib.Server(base_url)

class Slurper(object):
    
    def __init__(self, all_packages=False, package=None):
        if all_packages:
            self.package_names = PYPI.list_packages()
        elif package and not hasattr(package, '__iter__'):
            self.package_name = [package]
        elif package:
            self.package_name = package
        self.dumb_category, created = Category.objects.get_or_create(
                                title='dummy', slug='dummy')
        self.dumb_category.save()
        
    def get_latest_version(self, package_name, versions=None):
        if versions:
            return highest_version(versions)
        else:
            return highest_version(PYPI.package_releases(package_name))
        
    def get_or_create_package(self, package_name, version):
        data = PYPI.release_data(package_name, version)
        pypi_url = base_url + slugify(data['name'])
        package, created = Package.objects.get_or_create(
            title           = data['name'],
            slug            = slugify(data['name']),
            category        = self.dumb_category,
            pypi_url        = base_url + data['name']
        )
        package.repo_description = data['summary'] or data['description']
        if not package.repo_url:
            url = data.get("home_page", None) or data.get('project_url',"") or pypi_url
            # TODO - do some github cleanup so that 
            #           github.com/pydanny/django-uni-form/master 
            #           will cleanup to github/pydanny/django-uni-form/
            package.repo_url = url
        package.save()
        return package
        
    def get_or_create_all_packages(self, package_limit=None):
        """ 
            gets or creates packages
        
                package_limit: None or Integer. Limits the number of packages
            
        """
        for i, package_name in enumerate(self.package_names):
            if package_limit and i > package_limit:
                break
            from pypi.tasks import get_package_pypi
            try:
                get_package_pypi.delay(package_name)
            except UnicodeDecodeError, UnicodeError:
                print package_name