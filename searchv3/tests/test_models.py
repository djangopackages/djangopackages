from django.test import TestCase
from model_bakery import baker

from searchv3.models import ItemType, SearchV3


class SearchV3ModelTest(TestCase):
    def test_is_grid_returns_true(self):
        obj = baker.make(SearchV3, item_type=ItemType.GRID)
        self.assertTrue(obj.is_grid)

    def test_is_grid_package_returns_false(self):
        obj = baker.make(SearchV3, item_type=ItemType.PACKAGE)
        self.assertFalse(obj.is_grid)

    def test_get_absolute_url_package(self):
        obj = baker.make(SearchV3, item_type=ItemType.PACKAGE, slug="django-uni-form")
        self.assertEqual(obj.get_absolute_url(), "/packages/p/django-uni-form/")

    def test_get_absolute_url_grid(self):
        obj = baker.make(SearchV3, item_type=ItemType.GRID, slug="testing-grids")
        self.assertEqual(obj.get_absolute_url(), "/grids/g/testing-grids/")
