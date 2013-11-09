from django.test import TestCase

from package.utils import uniquer, normalize_license


class UtilsTest(TestCase):
    def test_uniquer(self):
        items = ['apple', 'apple', 'apple', 'banana', 'cherry']
        unique_items = ['apple', 'banana', 'cherry']
        self.assertEqual(uniquer(items), unique_items)

    def test_normalize_license(self):
        self.assertEqual(normalize_license(None), "UNKNOWN")
        self.assertEqual(
                normalize_license("""License :: OSI Approved :: MIT License
                """),
                "License :: OSI Approved :: MIT License")
        self.assertEqual(normalize_license("Pow" * 80), "Custom")
        self.assertEqual(normalize_license("MIT"), "MIT")
