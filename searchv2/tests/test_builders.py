from package.tests import initial_data
from searchv2.builders import build_1
from searchv2.models import SearchV2


def test_build_1_count(db):
    initial_data.load()
    assert SearchV2.objects.count() == 0
    build_1()
    assert SearchV2.objects.count() == 6
