from django.conf import settings
from django.test import TestCase

from searchv2.utils import remove_prefix, clean_title


class UtilFunctionTest(TestCase):

    def setUp(self):
        self.values = []
        for value in ["-me", ".me", "/me", "_me"]:
            value = f"{settings.PACKAGINATOR_SEARCH_PREFIX.lower()}{value}"
            self.values.append(value)

    def test_remove_prefix(self):
        for value in self.values:
            self.assertEqual(remove_prefix(value), "me")

    def test_clean_title(self):
        test_value = f"{settings.PACKAGINATOR_SEARCH_PREFIX.lower()}me"
        for value in self.values:
            self.assertEqual(clean_title(value), test_value)
