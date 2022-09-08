from django.core.management import call_command

from grid.models import Grid
from package.models import Package
from package.tests import initial_data
from searchv2.models import SearchV2


def test_searchv2_build(db):
    initial_data.load()

    assert SearchV2.objects.all().count() == 0

    grid_count = Grid.objects.all().count()
    package_count = Package.objects.all().count()

    call_command("searchv2_build")

    # TODO: Revisit this, but for now our total search results should be
    # all of our Grids and all of our Packages.

    search_count = SearchV2.objects.all().count()
    assert search_count == 6
    assert grid_count + package_count == search_count
