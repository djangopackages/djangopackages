"""Filters on the search results page narrow the matches without reranking."""

import re
from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone
from model_bakery import baker

from searchv3.models import ItemType, SearchV3

pytestmark = pytest.mark.django_db


@pytest.fixture()
def index():
    now = timezone.now()
    rows = {
        "app": baker.make(
            SearchV3,
            item_type=ItemType.PACKAGE,
            title="django-cache-app",
            slug="django-cache-app",
            description="cache helpers",
            category="App",
            repo_watchers=50,
            pypi_downloads=10,
            last_released=now - timedelta(days=400),
            last_committed=now - timedelta(days=1),
            weight=10,
        ),
        "framework": baker.make(
            SearchV3,
            item_type=ItemType.PACKAGE,
            title="django-cache-framework",
            slug="django-cache-framework",
            description="cache framework",
            category="Framework",
            repo_watchers=500,
            pypi_downloads=1000,
            last_released=now - timedelta(days=2),
            last_committed=now - timedelta(days=300),
            weight=5,
        ),
        "grid": baker.make(
            SearchV3,
            item_type=ItemType.GRID,
            title="Caching",
            slug="caching",
            description="cache comparison grid",
            category="",
            weight=1,
        ),
        "other": baker.make(
            SearchV3,
            item_type=ItemType.PACKAGE,
            title="django-unrelated",
            slug="django-unrelated",
            description="nothing to do with it",
            category="App",
        ),
    }
    return rows


def slugs(response):
    return [row.slug for row in response.context["search_results"]]


def get(client, **params):
    return client.get(reverse("search_results"), {"q": "cache", **params})


def test_no_filter_returns_everything_that_matches(client, index):
    response = get(client)

    assert set(slugs(response)) == {
        "django-cache-app",
        "django-cache-framework",
        "caching",
    }
    assert response.context["current_type"] == "all"
    assert response.context["current_sort"] == "relevance"


def test_type_narrows_to_packages_or_grids(client, index):
    assert set(slugs(get(client, type="package"))) == {
        "django-cache-app",
        "django-cache-framework",
    }
    assert slugs(get(client, type="grid")) == ["caching"]


def test_category_narrows_packages(client, index):
    assert slugs(get(client, category="Framework")) == ["django-cache-framework"]


def test_bad_values_fall_back_to_defaults(client, index):
    response = get(client, type="nope", sort="sideways")

    assert len(slugs(response)) == 3
    assert response.context["current_type"] == "all"
    assert response.context["current_sort"] == "relevance"


@pytest.mark.parametrize(
    ("sort", "first"),
    [
        ("stars", "django-cache-framework"),
        ("downloads", "django-cache-framework"),
        ("released", "django-cache-framework"),
        ("committed", "django-cache-app"),
    ],
)
def test_sorts_reorder_the_matches(client, index, sort, first):
    response = get(client, type="package", sort=sort)

    assert slugs(response)[0] == first
    assert set(slugs(response)) == {"django-cache-app", "django-cache-framework"}


def test_counts_are_over_all_matches_not_the_filtered_set(client, index):
    response = get(client, type="grid")

    counts = {item["value"]: item["count"] for item in response.context["type_filters"]}
    assert counts == {"all": 3, "package": 2, "grid": 1}


def test_category_chips_list_each_category_with_counts(client, index):
    response = get(client)

    chips = {
        item["label"]: item["count"] for item in response.context["category_filters"]
    }
    assert chips == {"All categories": 2, "App": 1, "Framework": 1}


def test_grids_have_no_category_chips(client, index):
    response = get(client, type="grid")

    assert "category_filters" not in response.context


def test_links_keep_the_other_filters_and_drop_defaults(client, index):
    response = get(client, type="package", category="App", sort="stars")

    grid_link = next(
        item["url"]
        for item in response.context["type_filters"]
        if item["value"] == "grid"
    )
    assert "type=grid" in grid_link
    assert "sort=stars" in grid_link
    assert "category=" not in grid_link  # grids have no category

    relevance_link = next(
        item["url"]
        for item in response.context["sort_options"]
        if item["value"] == "relevance"
    )
    assert "sort=" not in relevance_link
    assert "category=App" in relevance_link


def test_pagination_carries_the_filters(client, index):
    for i in range(25):
        baker.make(
            SearchV3,
            item_type=ItemType.PACKAGE,
            title=f"django-cache-extra-{i}",
            slug=f"django-cache-extra-{i}",
            description="cache",
            category="App",
        )

    response = get(client, type="package", sort="stars")

    assert response.context["is_paginated"]
    body = response.content.decode()
    next_link = re.search(r'href="([^"]*page=2)"', body).group(1)
    assert "type=package" in next_link
    assert "sort=stars" in next_link
    assert "q=cache" in next_link


def test_empty_query_shows_no_filters(client, index):
    response = client.get(reverse("search_results"), {"q": ""})

    assert response.status_code == 200
    assert "type_filters" not in response.context
