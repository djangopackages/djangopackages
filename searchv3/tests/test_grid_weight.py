from django.test import TestCase
from model_bakery import baker

from searchv3.builders import calc_grid_weight


class CalcGridWeightTest(TestCase):
    def test_locked_with_header_and_packages(self):
        grid = baker.make("grid.Grid", is_locked=True, header=True)
        grid.packages.add(baker.make("package.Package"))
        self.assertEqual(calc_grid_weight(grid=grid, max_weight=120), 100)

    def test_unlocked_deducts(self):
        grid = baker.make("grid.Grid", is_locked=False, header=True)
        grid.packages.add(baker.make("package.Package"))
        self.assertEqual(calc_grid_weight(grid=grid, max_weight=120), 80)

    def test_no_header_deducts(self):
        grid = baker.make("grid.Grid", is_locked=True, header=False)
        grid.packages.add(baker.make("package.Package"))
        self.assertEqual(calc_grid_weight(grid=grid, max_weight=120), 80)

    def test_no_packages_deducts(self):
        grid = baker.make("grid.Grid", is_locked=True, header=True)
        self.assertEqual(calc_grid_weight(grid=grid, max_weight=120), 80)

    def test_all_penalties(self):
        grid = baker.make("grid.Grid", is_locked=False, header=False)
        self.assertEqual(calc_grid_weight(grid=grid, max_weight=120), 40)

    def test_custom_max_weight(self):
        grid = baker.make("grid.Grid", is_locked=True, header=True)
        grid.packages.add(baker.make("package.Package"))
        self.assertEqual(calc_grid_weight(grid=grid, max_weight=60), 50)
