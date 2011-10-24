from datetime import datetime

from django.test import TestCase

from package.tests import data, initial_data
from searchv2.utils import remove_prefix, clean_title

class UtilFunctionTest(TestCase):  
        
    def test_remove_prefix(self):
        values = ["django-me","django.me","django/me","django_me"]
        for value in values:
            self.assertEqual(remove_prefix(value), "me")
            
    def test_clean_title(self):
        values = ["django-me","django.me","django/me","django_me"]
        for value in values:
            self.assertEqual(clean_title(value), "djangome")
        