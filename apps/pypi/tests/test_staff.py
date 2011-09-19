from django.template.defaultfilters import slugify
from django.test import TestCase

from package.models import Package
from pypi import staff

TEST_PACKAGE_REPO_NAME = 'django-uni-form'
TEST_STAFF = 'pydanny'
BAD_VALUE = 'sdfsefdgeth werwesfsegsfadsffdvdf  sofaeifjaejvdszv kSDV9839835tpiwoer[qe'

class StaffTests(TestCase):
        
    def test_get_package_staff(self):
        package_staff = staff.get_package_staff(TEST_PACKAGE_REPO_NAME)
        self.assertTrue(TEST_STAFF in package_staff)
        
    def test_bad_package_staff(self):
        package_staff = staff.get_package_staff(BAD_VALUE)
        self.assertFalse(package_staff)
        
    def test_get_user_packages(self):
        packages = staff.get_user_packages(TEST_STAFF)
        self.assertTrue(TEST_PACKAGE_REPO_NAME in packages)
        
    def test_bad_user_packages(self):
        packages = staff.get_package_staff(BAD_VALUE)
        self.assertFalse(packages)