from django.template.defaultfilters import slugify
from django.test import TestCase

from package.models import Package, Category
from pypi.models import PypiUpdateLog
from pypi.slurper import Slurper

TEST_PACKAGE_NAME = 'Django'
TEST_PACKAGE_VERSION = '1.2.5'
TEST_PACKAGE_REPO_NAME = 'django-uni-form'

class SlurpAllTests(TestCase):
    
    def setUp(self):
        self.slurper = Slurper()
    
    def test_package_names(self):
        
        self.assertTrue(len(self.slurper.package_names) > 1000)
        self.assertTrue(TEST_PACKAGE_NAME in self.slurper.package_names)
        
    def test_get_latest_version(self):
        
        version = self.slurper.get_latest_version(TEST_PACKAGE_NAME)
        self.assertEquals(version, TEST_PACKAGE_VERSION)
        
    def test_get_or_create_package(self):
        
        version = self.slurper.get_latest_version(TEST_PACKAGE_NAME)
        package = self.slurper.get_or_create_package(TEST_PACKAGE_NAME, version)
        self.assertTrue(isinstance(package, Package))
        self.assertEquals(package.title, TEST_PACKAGE_NAME)
        self.assertEquals(package.slug, slugify(TEST_PACKAGE_NAME))
        
    def test_get_or_create_with_repo(self):

        version = self.slurper.get_latest_version(TEST_PACKAGE_REPO_NAME)        
        package = self.slurper.get_or_create_package(TEST_PACKAGE_REPO_NAME, version)
        self.assertTrue(isinstance(package, Package))
        self.assertEquals(package.title, TEST_PACKAGE_REPO_NAME)
        self.assertEquals(package.slug, slugify(TEST_PACKAGE_REPO_NAME))
        
    def test_get_or_create_all_packages(self):
        
        self.slurper.get_or_create_all_packages(10)
        print Package.objects.all()