from django.test import TestCase

from grid.models import Grid
from package.models import Package
from package.tests import initial_data
from searchv3.builders import build_search_index
from searchv3.models import ItemType, SearchV3


class BuildSearchIndexTest(TestCase):
    def setUp(self):
        initial_data.load()

    def test_total_count_matches_packages_plus_grids(self):
        build_search_index()
        grid_count = Grid.objects.count()
        package_count = Package.objects.count()
        self.assertEqual(SearchV3.objects.count(), grid_count + package_count)

    def test_all_vectors_populated(self):
        build_search_index()
        null_vectors = SearchV3.objects.filter(search_vector__isnull=True).count()
        self.assertEqual(null_vectors, 0)

    def test_deleted_package_removed_from_index(self):
        build_search_index()
        self.assertTrue(
            SearchV3.objects.filter(
                item_type=ItemType.PACKAGE, slug="testability"
            ).exists()
        )

        Package.objects.get(slug="testability").delete()
        build_search_index()

        self.assertFalse(
            SearchV3.objects.filter(
                item_type=ItemType.PACKAGE, slug="testability"
            ).exists()
        )

    def test_deleted_grid_removed_from_index(self):
        build_search_index()
        self.assertTrue(
            SearchV3.objects.filter(item_type=ItemType.GRID, slug="testing").exists()
        )

        Grid.objects.get(slug="testing").delete()
        build_search_index()

        self.assertFalse(
            SearchV3.objects.filter(item_type=ItemType.GRID, slug="testing").exists()
        )
