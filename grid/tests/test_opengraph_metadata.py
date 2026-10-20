"""Grid pages used to fall back to the generic logo card.

grid_detail.html had no metadata block, so every grid advertised the same
image even though grid_opengraph has been rendering a real one all along.
"""

import re
from urllib.parse import quote_plus

import pytest
from django.urls import reverse


def meta_count(content, prop):
    return content.decode().count(f'<meta property="{prop}"')


def og_image(content):
    match = re.search(r'<meta property="og:image" content="([^"]+)"', content.decode())
    return match.group(1) if match else ""


@pytest.mark.django_db
def test_grid_detail_points_at_its_own_opengraph_image(grid, client):
    response = client.get(reverse("grid", kwargs={"slug": grid.slug}))

    assert response.status_code == 200
    # page_metadata hands the path to the screenshot service, so the grid's
    # own opengraph URL shows up inside it quoted.
    assert quote_plus(grid.get_opengraph_image_url()) in og_image(response.content)


@pytest.mark.django_db
def test_grid_detail_is_not_the_generic_card(grid, client):
    response = client.get(reverse("grid", kwargs={"slug": grid.slug}))

    assert "open_graph.png" not in og_image(response.content)


@pytest.mark.django_db
def test_grid_detail_uses_the_grid_title(grid, client):
    response = client.get(reverse("grid", kwargs={"slug": grid.slug}))

    assert f'<meta property="og:title" content="Django Packages : {grid.title}"'.encode() in response.content


@pytest.mark.django_db
def test_grid_detail_emits_one_set_of_tags(grid, client):
    response = client.get(reverse("grid", kwargs={"slug": grid.slug}))

    assert meta_count(response.content, "og:title") == 1
    assert meta_count(response.content, "og:image") == 1


@pytest.mark.django_db
def test_grid_packages_emits_one_set_of_tags(grid, client):
    """It called page_metadata twice, so the page shipped two of everything."""
    response = client.get(reverse("grid_packages", kwargs={"slug": grid.slug}))

    assert response.status_code == 200
    assert meta_count(response.content, "og:title") == 1
    assert meta_count(response.content, "og:image") == 1


@pytest.mark.django_db
def test_the_card_does_not_advertise_a_dead_domain(grid, client):
    """It printed djangogrids.org, which has no DNS record at all."""
    response = client.get(reverse("grid_opengraph", kwargs={"slug": grid.slug}))

    assert response.status_code == 200
    assert b"djangogrids.org" not in response.content
    assert f'https://djangopackages.org/grids/g/{grid.slug}/'.encode() in response.content
