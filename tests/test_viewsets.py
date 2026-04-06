import pytest
from django.urls import reverse
from model_bakery import baker
from rest_framework import status

from grid.models import GridPackage
from package.models import Package, Version

# PackageViewSet Tests


@pytest.mark.django_db
def test_package_list_get(client, category, django_assert_num_queries):
    packages = [
        baker.make(
            Package,
            category=category,
            repo_url=f"https://github.com/django/test-pkg-{i}",
        )
        for i in range(5)
    ]
    for pkg in packages:
        pkg.latest_version = baker.make(Version, package=pkg)
        pkg.save(update_fields=["latest_version"])
        baker.make(GridPackage, package=pkg, _quantity=3)

    url = reverse("apiv4:package-list")

    with django_assert_num_queries(4):
        response = client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data["results"]) == 5


@pytest.mark.django_db
def test_package_retrieve_pk_get(client, category, django_assert_num_queries):
    pkg = baker.make(
        Package,
        category=category,
        repo_url="https://github.com/django/test-detail-pkg",
    )
    pkg.latest_version = baker.make(Version, package=pkg)
    pkg.save(update_fields=["latest_version"])
    baker.make(GridPackage, package=pkg, _quantity=5)

    url = reverse("apiv4:package-detail", kwargs={"pk_or_slug": pkg.pk})

    with django_assert_num_queries(3):
        response = client.get(url)

    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_package_retrieve_slug_get(client, category, django_assert_num_queries):
    pkg = baker.make(
        Package,
        category=category,
        repo_url="https://github.com/django/test-slug-pkg",
    )
    pkg.latest_version = baker.make(Version, package=pkg)
    pkg.save(update_fields=["latest_version"])
    baker.make(GridPackage, package=pkg, _quantity=5)

    url = reverse("apiv4:package-detail", kwargs={"pk_or_slug": pkg.slug})

    with django_assert_num_queries(3):
        response = client.get(url)

    assert response.status_code == status.HTTP_200_OK


# SearchV3ViewSet Tests


@pytest.mark.django_db
def test_searchv3_list_get(client):
    url = reverse("apiv4:search-list")
    response = client.get(url)
    assert response.status_code == status.HTTP_200_OK


# GridViewSet Tests


@pytest.mark.django_db
def test_grid_list_get(client, grid):
    url = reverse("apiv4:grid-list")
    response = client.get(url)
    assert len(response.data["results"]) == 1
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_grid_retrieve_pk_get(client, grid):
    url = reverse("apiv4:grid-detail", kwargs={"pk_or_slug": grid.pk})
    response = client.get(url)
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_grid_retrieve_slug_get(client, grid):
    url = reverse("apiv4:grid-detail", kwargs={"pk_or_slug": grid.slug})
    response = client.get(url)
    assert response.status_code == status.HTTP_200_OK


# CategoryViewSet Tests


@pytest.mark.django_db
def test_category_list_get(client, category):
    url = reverse("apiv4:category-list")
    response = client.get(url)
    assert len(response.data["results"]) == 1
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_category_retrieve_get(client, category):
    url = reverse("apiv4:category-detail", kwargs={"pk": category.pk})
    response = client.get(url)
    assert response.status_code == status.HTTP_200_OK
