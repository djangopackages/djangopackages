#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
PyPI interface (see http://wiki.python.org/moin/PyPiXmlRpc)
"""

from datetime import datetime
import itertools
import xmlrpclib

from django.template.defaultfilters import slugify

from package.models import Package, Version
from pypi.models import PypiUpdateLog

PYPI = xmlrpclib.Server('http://pypi.python.org/pypi')

class Slurper(object):
    
    def __init__(self):
        self.package_names = PYPI.list_packages()

    
    
    
