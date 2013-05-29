#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
PyPI information fetcher per repo
"""

from datetime import datetime
import locale
import xmlrpclib

from distutils.version import StrictVersion, LooseVersion
import requests

from core.utils import status_choices_switch

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
            release_data.downloads += download["downloads"]

            timetuple = download['upload_time'].timetuple()
            release_data.upload_time = datetime(
                timetuple.tm_year,
                timetuple.tm_mon,
                timetuple.tm_mday,
                timetuple.tm_hour,
                timetuple.tm_min,
                timetuple.tm_sec,
            )

        if release_data.license == None or 'UNKNOWN' == release_data.license.upper():
            for classifier in release_data.classifiers:
                if classifier.startswith('License'):
                    # Do it this way to cover people not quite following the spec
                    # at http://docs.python.org/distutils/setupscript.html#additional-meta-data
                    release_data.license = classifier.replace('License ::', '')
                    release_data.license = release_data.license.replace('OSI Approved :: ', '')
                    break

        if release_data.license and len(release_data.license) > 100:
            release_data.license = "Other (see http://pypi.python.org/pypi/%s)" % package_name

        release_data.development_status = 0
        for classifier in release_data.classifiers:
            if classifier.startswith('Development Status'):
                release_data.development_status = status_choices_switch(classifier)
                break

        releases.append(release_data)
    return releases


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
