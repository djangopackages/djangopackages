from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase

from package.pypi import fetch_releases
from apps.package.models import Package

class GitHubTest(TestCase):

    fixtures = ['test_initial_data.json']

    def setUp(self):
        # package list is needed throughout the app
        self.packages = Package.objects.all()

    def _resetting_packages(self, ):
        for package in packages:
            package.repo_watchers = 0
            package.repo_forks = 0
            package.repo_description = ''
            package.participants = ''

    def _is_package_empty(self, package):
        self.assertGreater(package.repo_watchers, 0)
        self.assertGreater(package.repo_forks, 0)
        self.assertGreater(package.repo_description, '')
        self.assertGreater(package.participants, '')

    def test_initial_data(self):
        for package in self.packages:
            self.assertTrue(package.repo)

    def test_repo_handler_fetch(self):

        # resetting package metadata
        self._resetting_packages()

        for package in packages:
            handler = package.repo #__import__(self.repo.handler)

            #fetching meta data from repo
            pulled_package = handler.fetch_metadata(package)

            # check if package metadata is not empty or incorrect
            self._is_package_empty(pulled_package)


    def test_package_pypi_fetch(self):
        
        for package in self.packages:

            # fetch package releases from pypi
            releases = fetch_releases(package.pypi_name)

            # make sure that package number is bigger than 0
            self.assertGreater(len(releases), 0)

            for release in releases:

                self.assertTrue(isinstance(release.downloads, int))
                self.assertTrue(isinstance(release._pypi_hidden, bool))

    def test_package_model_fetch(self):

        # reset package metadata
        self._resetting_packages()

        for package in self.packages:

            # method being tested, which fills in the metadata fields
            package.fetch_metadata()

            # check that package metadata is not empty or incorrect
            self._is_package_empty(package)
