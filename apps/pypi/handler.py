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

def fetch_package_list():
    """Fetches the list of all packages on PyPI."""
    return PYPI.list_packages()

def fetch_package_releases(package_name, include_hidden=True):
    """Fetches the list of releases for a package."""
    return PYPI.package_releases(package_name, include_hidden)

def fetch_release_urls(package_name, version):
    """Fetches the release URL data for a package."""
    return PYPI.release_urls(package_name, version)

def fetch_release_data(package_name, version):
    """Returns the metadata for a package."""
    return PYPI.release_data(package_name, version)

def fetch_changelog(timestamp):
    """Returns the list of package releases updated since timestamp."""
    return PYPI.changelog(timestamp)

def update_outdated_packages(allow_initial_full_download=False):
    """
    Updates all packages updated since the last update.
    
    By default, if there is no update log, we assume you don't have any
    package data yet and throw an error. If you really want to do an initial
    pull of ALL data from PyPI -- this will take a LONG TIME -- you can pass
    in the flag allow_initial_full_download as True.
    """
    # Set the update log first, so if anything, we overlap rather than miss
    # out on any updates
    updates_exist = PypiUpdateLog.objects.exists()
    update_log = PypiUpdateLog()
    update_log.save()

    if not updates_exist:
        if allow_initial_full_download:
            names_to_update = PYPI.list_packages()
        else:
            raise ValueError('There is no existing PyPI package data. If you '
                'are certain you want to pull all PyPI data and you totally '
                'know what you\'re doing, please pass the appropriate flag.')
    else:
        last_update = PypiUpdateLog.last_update()
        changelog = fetch_changelog(last_update)
        names_to_update = set(map(lambda action: action[0], changelog))

    # Grab the changelog and farm each update out
    for name in names_to_update:
        update_or_create_package(name)

def update_or_create_package(package_name):
    """Updates the download total and metadata for a package."""
    package_data = {
        'versions': [],
        'downloads': 0,
        'latest': {},
    }

    versions = fetch_package_releases(package_name)
    print versions
    # Iterate over versions from oldest to newest
    for i, version in enumerate(reversed(versions)):
        # Fetch the version metadata
        data = fetch_release_data(package_name, version)
        # Cover people not quite following the spec:
        # docs.python.org/distutils/setupscript.html#additional-meta-data
        if data.get('license', 'unknown').lower() == 'unknown':
            for classifier in data['classifiers']:
                if classifier.startswith('License'):
                    data['license'] = classifier.replace('License ::', '')
                    break
        data['license'] = data['license'].replace('OSI Approved ::', '')
        data['license'] = data['license'].strip()

        version_data = {
            'order': i,
            'number': version,
            'downloads': 0,
            'license': data['license'][:100],
            'hidden': bool(data.get('_pypi_hidden')),
        }

        # Increment the download totals
        release_urls = fetch_release_urls(package_name, version)
        for release_url in release_urls:
            version_data['downloads'] += int(release_url.get('downloads', 0))

        package_data['versions'].append(version_data)
        package_data['downloads'] += version_data['downloads']

        # The last version is always the most recent, so keep that one
        package_data['latest'] = data

    # Update everything in the database
    package, created = Package.objects.get_or_create(
        pypi_url=package_name,
        defaults={
            'pypi_url': package_name,
            'title': package_data['latest'].get('name'),
            'slug': slugify(package_data['latest'].get('name'))
        }
    )
    package.pypi_home_page = package_data['latest'].get('home_page')
    package.pypi_downloads = package_data['downloads']
    package.pypi_updated_ts = datetime.utcnow()
    package.save()
    for version_data in package_data['versions']:
        version, created = Version.objects.get_or_create(
            package=package,
            number=version_data['number'],
            defaults={
                'package': package,
                'number': version_data['number'],
                'order': version_data['order'],
            }
        )
        version.order = version_data['order']
        version.downloads = version_data['downloads']
        version.license = version_data['license']
        version.hidden = version_data['hidden']
        version.save()