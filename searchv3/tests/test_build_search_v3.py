from django.core.management import call_command
from django.test import TestCase

from package.tests import initial_data
from searchv3.models import SearchV3


class BuildSearchV3CommandTest(TestCase):
    def setUp(self):
        initial_data.load()

    def test_indexes_all_items(self):
        self.assertEqual(SearchV3.objects.count(), 0)
        call_command("build_search_v3")
        self.assertEqual(SearchV3.objects.count(), 6)

    def test_idempotent(self):
        call_command("build_search_v3")
        call_command("build_search_v3")
        self.assertEqual(SearchV3.objects.count(), 6)
