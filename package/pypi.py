#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
PyPI information fetcher per repo
"""


import locale


from distutils.version import StrictVersion, LooseVersion
import requests


locale.setlocale(locale.LC_ALL, '')


class PypiVersion(object):

    def __init__(self, release_data):
        self.__dict__.update(release_data)


def fetch_licenses():
    response = requests.get("http://pypi.python.org/pypi?%3Aaction=list_classifiers")
    is_license = lambda x: x.startswith('License')
    classifiers = response.content.splitlines()
    return filter(is_license, classifiers)


def compare_versions(version1, version2):
    """ Determines the order of versions"""
    try:
        return cmp(StrictVersion(version1), StrictVersion(version2))
    # in case of abnormal version number, fall back to LooseVersion
    except ValueError:
        return cmp(LooseVersion(version1), LooseVersion(version2))


def highest_version(versions):
    """ returns the highest version """
    return reduce((lambda v1, v2: compare_versions(v1, v2) == 1 and v1 or v2), versions)
