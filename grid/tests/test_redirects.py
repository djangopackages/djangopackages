import pytest
from django.contrib.redirects.models import Redirect
from django.contrib.sites.models import Site


@pytest.mark.django_db
def test_redirect_row_answers_a_404(client):
    Redirect.objects.create(
        site=Site.objects.get_current(),
        old_path="/grids/g/static-builders/",
        new_path="/grids/g/static-site-generators/",
    )

    response = client.get("/grids/g/static-builders/")

    assert response.status_code == 301
    assert response["Location"] == "/grids/g/static-site-generators/"


@pytest.mark.django_db
def test_unknown_grid_still_404s(client):
    assert client.get("/grids/g/does-not-exist/").status_code == 404
