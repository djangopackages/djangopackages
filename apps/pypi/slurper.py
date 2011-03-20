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

base_url = "http://pypi.python.org/pypi/"
PYPI = xmlrpclib.Server(base_url)

class Slurper(object):
    
    def __init__(self):
        self.package_names = PYPI.list_packages()
        self.dumb_category, created = Category.objects.get_or_create(
                                title='Python', slug='python')
        self.dumb_category.save()
        
    def get_latest_version_number(self, package_name, versions=None):
        if versions:
            return highest_version(versions)
        else:
            return highest_version(PYPI.package_releases(package_name))
        
    def get_or_create_package(self, package_name, version):
        data = PYPI.release_data(package_name, version)
        pypi_url = base_url + package_name
        package, created = Package.objects.get_or_create(
            title           = data['name'],
            slug            = slugify(package_name),
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
        
    def get_versions(self, package_name):        
        try:
            package = Package.objects.get(slug=slugify(package_name))
        except Package.DoesNotExist:
            # Maybe doesn't exist yet so we skip it in this batch
            return False
        
        package.fetch_metadata()
        return True
        
            
        
        
    def get_or_create_all_packages(self, package_limit=None):
        """ 
            gets or creates packages
        
                package_limit: None or Integer. Limits the number of packages
            
        """
        for i, package_name in enumerate(self.package_names):
            if package_limit and i > package_limit:
                break
            versions = PYPI.package_releases(package_name)
            highest_version = self.get_latest_version_number(package_name, versions)
            package = self.get_or_create_package(package_name, highest_version)            
            print package
            for version in versions:
                if version == highest_version:
                    continue
                print version