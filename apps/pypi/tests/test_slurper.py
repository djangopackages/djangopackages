from django.template.defaultfilters import slugify
from django.test import TestCase

from package.models import Package, Version
from pypi.slurper import Slurper

TEST_PACKAGE_NAME = 'Django'
TEST_PACKAGE_VERSION = '1.2.5'
TEST_PACKAGE_REPO_NAME = 'django-uni-form'

class SlurpAllTests(TestCase):
            
    def test_get_latest_version_number(self):
        
        slurper = Slurper(TEST_PACKAGE_NAME)
        version = slurper.get_latest_version_number(TEST_PACKAGE_NAME)
        self.assertEquals(version, TEST_PACKAGE_VERSION)

    def test_get_or_create_package(self):
        
        slurper = Slurper(TEST_PACKAGE_NAME)
        version = slurper.get_latest_version_number(TEST_PACKAGE_NAME)
        package, created = slurper.get_or_create_package(TEST_PACKAGE_NAME, version)
        self.assertTrue(created)
        self.assertTrue(isinstance(package, Package))
        self.assertEquals(package.title, TEST_PACKAGE_NAME)
        self.assertEquals(package.slug, slugify(TEST_PACKAGE_NAME))

    def test_get_or_create_with_repo(self):

        slurper = Slurper(TEST_PACKAGE_REPO_NAME)
        version = slurper.get_latest_version_number(TEST_PACKAGE_REPO_NAME)        
        package, created = slurper.get_or_create_package(TEST_PACKAGE_REPO_NAME, version)
        self.assertTrue(created)        
        self.assertTrue(isinstance(package, Package))
        self.assertEquals(package.title, TEST_PACKAGE_REPO_NAME)
        self.assertEquals(package.slug, slugify(TEST_PACKAGE_REPO_NAME))


    def test_check_versions(self):
        
        slurper = Slurper(TEST_PACKAGE_REPO_NAME)        
        version = slurper.get_latest_version_number(TEST_PACKAGE_REPO_NAME)
                
        # make me a package (Actually, make me a billionare)
        slurper.get_or_create_package(TEST_PACKAGE_REPO_NAME, version)
                
        # fetch the package for testing
        package = Package.objects.get(title=TEST_PACKAGE_REPO_NAME)
        
        self.assertTrue(package.pypi_downloads > 1000)