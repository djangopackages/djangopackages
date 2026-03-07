import pytest
from django.urls import reverse
from model_bakery import baker
from rest_framework import status
from waffle.testutils import override_flag

from apiv4.serializers import SearchV3Serializer
from searchv3.models import ItemType, SearchV3

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


# SearchV3Serializer backward-compatibility tests


@pytest.mark.django_db
def test_searchv3_serializer_includes_absolute_url_for_package():
    """SearchV3Serializer must expose absolute_url for backward compatibility with SearchV2."""
    obj = baker.make(SearchV3, item_type=ItemType.PACKAGE, slug="django-environ")
    data = SearchV3Serializer(obj).data
    assert "absolute_url" in data
    assert data["absolute_url"] == "/packages/p/django-environ/"


@pytest.mark.django_db
def test_searchv3_serializer_includes_absolute_url_for_grid():
    """SearchV3Serializer must expose absolute_url for grid items too."""
    obj = baker.make(SearchV3, item_type=ItemType.GRID, slug="auth-tools")
    data = SearchV3Serializer(obj).data
    assert "absolute_url" in data
    assert data["absolute_url"] == "/grids/g/auth-tools/"


@pytest.mark.django_db
def test_searchv3_serializer_absolute_url_empty_for_unknown_type():
    """get_absolute_url returns an empty string for unrecognised item types."""
    obj = baker.make(SearchV3, item_type=ItemType.PACKAGE, slug="test-pkg")
    # Override item_type in-memory (not persisted) to simulate an edge case.
    obj.item_type = "unknown"
    data = SearchV3Serializer(obj).data
    assert data["absolute_url"] == ""


@pytest.mark.django_db
@override_flag("use_searchv3", active=True)
def test_searchv3_api_response_includes_absolute_url(client):
    """The /api/v4/search/ endpoint must include absolute_url in every result."""
    baker.make(
        SearchV3,
        item_type=ItemType.PACKAGE,
        title="django-crispy-forms",
        slug="django-crispy-forms",
    )
    url = reverse("apiv4:search-list")
    response = client.get(url, {"q": "django-crispy-forms"})
    assert response.status_code == status.HTTP_200_OK
    results = response.data["results"]
    assert len(results) > 0
    assert "absolute_url" in results[0]
    assert results[0]["absolute_url"] == "/packages/p/django-crispy-forms/"
