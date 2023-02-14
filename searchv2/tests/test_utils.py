from django.conf import settings

from searchv2.utils import clean_title, remove_prefix


def test_search_v2_utils_remove_prefix(db):
    values = []
    for value in ["-me", ".me", "/me", "_me"]:
        value = f"{settings.PACKAGINATOR_SEARCH_PREFIX.lower()}{value}"
        values.append(value)

    for value in values:
        assert remove_prefix(value) == "me"


def test_search_v2_utils_clean_title(db):
    values = []
    for value in ["-me", ".me", "/me", "_me"]:
        value = f"{settings.PACKAGINATOR_SEARCH_PREFIX.lower()}{value}"
        values.append(value)

    test_value = f"{settings.PACKAGINATOR_SEARCH_PREFIX.lower()}me"

    for value in values:
        assert clean_title(value) == test_value
