import pytest
from django.urls import reverse

from grid.urls import RENAMED_GRIDS


@pytest.mark.parametrize(("old", "new"), sorted(RENAMED_GRIDS.items()))
def test_renamed_grid_redirects_permanently(client, old, new):
    response = client.get(f"/grids/g/{old}/")

    assert response.status_code == 301
    assert response["Location"] == reverse("grid", kwargs={"slug": new})


def test_renamed_grid_redirect_keeps_query_string(client):
    response = client.get("/grids/g/static-builders/?sort=stars")

    assert response.status_code == 301
    assert response["Location"] == "/grids/g/static-site-generators/?sort=stars"
