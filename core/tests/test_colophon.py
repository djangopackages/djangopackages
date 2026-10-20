"""The colophon used to live at /stack/, so the old URL has to keep working."""

import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_colophon_renders(client):
    response = client.get(reverse("colophon"))

    assert response.status_code == 200
    assert "colophon.html" in [template.name for template in response.templates]


@pytest.mark.django_db
def test_stack_permanently_redirects_to_colophon(client):
    response = client.get(reverse("stack"))

    assert response.status_code == 301
    assert response["Location"] == reverse("colophon")


@pytest.mark.django_db
def test_the_footer_links_to_it(client):
    response = client.get(reverse("colophon"))

    assert f'href="{reverse("colophon")}"'.encode() in response.content
