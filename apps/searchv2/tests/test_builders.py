from datetime import datetime

from django.test import TestCase

from package.models import Package
from package.tests import data, initial_data
from searchv2.models import SearchV2
from searchv2.builders import build_1

class BuilderTest(TestCase):  
    
    def setUp(self):
        initial_data.load()    
        
    def test_build_1_count(self):
        self.assertEquals(SearchV2.objects.count(), 0)
        build_1(False)
        self.assertEquals(SearchV2.objects.count(), 6)