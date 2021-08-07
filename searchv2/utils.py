from django.conf import settings
from django.template.defaultfilters import slugify

CHARS = ["_", ",", ".", "-", " ", "/", "|"]


def remove_prefix(value):
    value = value.lower()
    for char in CHARS:
        value = value.replace(f"{settings.PACKAGINATOR_SEARCH_PREFIX.lower()}{char}", "")
    return value


def clean_title(value):
    value = slugify(value)
    for char in CHARS:
        value = value.replace(char, "")
    return value
