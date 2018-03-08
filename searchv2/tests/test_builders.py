from django.test import TestCase

from package.tests import initial_data
from searchv2.models import SearchV2
from searchv2.builders import build_1


class BuilderTest(TestCase):

    def setUp(self):
        initial_data.load()

    def test_build_1_count(self):
        self.assertEqual(SearchV2.objects.count(), 0)
        build_1()
        self.assertEqual(SearchV2.objects.count(), 6)
