import pytest
from django.urls import reverse
from rest_framework import status

# PackageViewSet Tests


@pytest.mark.django_db
def test_package_list_get(client, package):
    url = reverse("apiv4:package-list")
    response = client.get(url)
    assert len(response.data["results"]) == 1
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_package_retrieve_pk_get(client, package):
    url = reverse("apiv4:package-detail", kwargs={"pk_or_slug": package.pk})
    response = client.get(url)
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_package_retrieve_slug_get(client, package):
    url = reverse("apiv4:package-detail", kwargs={"pk_or_slug": package.slug})
    response = client.get(url)
    assert response.status_code == status.HTTP_200_OK


# SearchV2ViewSet Tests


@pytest.mark.django_db
def test_searchv2_list_get(client):
    url = reverse("apiv4:searchv2-list")
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
