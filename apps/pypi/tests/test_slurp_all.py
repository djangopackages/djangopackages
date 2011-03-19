from django.test import TestCase

from package.models import Package
from pypi.models import PypiUpdateLog
from pypi.slurp_all import Slurper

class SlurpAllTests(TestCase):
    
    def test_package_names(self):
        
        slurper = Slurper()
        self.assertTrue(len(slurper.package_names) > 1000)
        self.assertTrue('Django' in slurper.package_names)