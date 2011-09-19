from django.test import TestCase
from package.utils import uniquer

class UtilsTest(TestCase):
    def test_uniquer(self):
        items = ['apple', 'apple', 'apple', 'banana', 'cherry']
        unique_items = ['apple', 'banana', 'cherry']
        self.assertEqual(uniquer(items), unique_items)
