"""Homepage category cards are ordered by size, except for the catch-all.

These call HomepageView._get_categories directly rather than fetching the
page. Ordering is all that changed, and a request would read waffle flags,
which warms a cache shared across the session and shifts the query counts
other tests assert on.
"""

import pytest
from django.core.cache import cache
from model_bakery import baker

from homepage.views import HomepageView
from package.models import Category, Package


@pytest.fixture()
def categories(db):
    cache.delete("categories")

    # Migrations ship categories of their own, and an empty one would still
    # take a slot in the order being asserted on.
    Package.objects.all().delete()
    Category.objects.all().delete()

    for slug, count in {
        "apps": 40,
        "other": 30,
        "projects": 5,
        "deployment": 2,
    }.items():
        category = Category.objects.create(slug=slug, title=slug, title_plural=slug)
        for i in range(count):
            baker.make(
                Package,
                slug=f"{slug}-{i}",
                title=f"{slug} {i}",
                category=category,
                repo_url=f"https://github.com/example/{slug}-{i}",
            )


def ordered_slugs():
    cache.delete("categories")
    return [category.slug for category in HomepageView()._get_categories()]


@pytest.mark.django_db
def test_other_goes_last_even_though_it_is_second_biggest(categories):
    assert ordered_slugs() == ["apps", "projects", "deployment", "other"]


@pytest.mark.django_db
def test_the_counts_still_come_back(categories):
    by_slug = {c.slug: c.package_count for c in HomepageView()._get_categories()}

    assert by_slug == {"apps": 40, "other": 30, "projects": 5, "deployment": 2}


@pytest.mark.django_db
def test_other_goes_last_even_when_it_is_the_smallest(categories):
    Package.objects.filter(category__slug="other").delete()

    assert ordered_slugs()[-1] == "other"


@pytest.mark.django_db
def test_no_other_category_is_fine(categories):
    # Package.category is PROTECT, so its packages go first.
    Package.objects.filter(category__slug="other").delete()
    Category.objects.filter(slug="other").delete()

    assert ordered_slugs() == ["apps", "projects", "deployment"]
