#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
PyPI information fetcher per repo
"""

from datetime import datetime
import locale
import sys
import xmlrpclib

locale.setlocale(locale.LC_ALL, '')

class PypiVersion(object):
    
    def __init__(self, release_data):
        self.__dict__.update(release_data)
        
def fetch_releases(package_name, include_hidden=True):
    
    if not package_name:
        raise TypeError("package_name requires a valid package name")
    
    package_name = package_name
    include_hidden = include_hidden
    proxy = xmlrpclib.Server('http://pypi.python.org/pypi')
            
    releases = []
    
    for version in proxy.package_releases(package_name, include_hidden):
        release_data = PypiVersion(proxy.release_data(package_name, version))
        release_data.hidden = release_data._pypi_hidden

        release_data.downloads = 0
        for download in proxy.release_urls(package_name, version):
            release_data.downloads +=  download["downloads"]
            
        releases.append(release_data)    
    return releases