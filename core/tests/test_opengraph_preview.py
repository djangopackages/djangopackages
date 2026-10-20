import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from model_bakery import baker


pytestmark = pytest.mark.django_db


@pytest.fixture()
def staff_user(db):
    return baker.make(User, username="og-staff", is_staff=True)


def test_anonymous_is_sent_to_login(client):
    response = client.get(reverse("opengraph_preview"))

    assert response.status_code == 302
    assert "/login/" in response["Location"]


def test_a_regular_user_is_forbidden(client):
    client.force_login(baker.make(User, username="og-regular", is_staff=False))

    assert client.get(reverse("opengraph_preview")).status_code == 403


def test_staff_can_see_it(client, staff_user):
    client.force_login(staff_user)

    response = client.get(reverse("opengraph_preview"))

    assert response.status_code == 200


def test_it_is_noindex(client, staff_user):
    """It is unlisted on purpose, so it should never be indexed."""
    client.force_login(staff_user)

    response = client.get(reverse("opengraph_preview"))

    assert b'name="robots" content="noindex, nofollow"' in response.content


def test_it_is_not_in_the_sitemap(client):
    response = client.get("/sitemap-static.xml")

    assert b"opengraph/preview" not in response.content


def test_each_card_type_is_previewed(client, staff_user, package, grid):
    """One of each: package, grid, profile."""
    client.force_login(staff_user)

    response = client.get(reverse("opengraph_preview"))
    content = response.content.decode()

    assert ">Package</h2>" in content
    assert ">Grid</h2>" in content
    assert ">Profile</h2>" in content


def test_a_card_links_to_its_own_opengraph_page(client, staff_user, package):
    client.force_login(staff_user)

    response = client.get(reverse("opengraph_preview"))

    assert package.get_opengraph_image_url().encode() in response.content


def test_the_fallback_image_is_shown(client, staff_user):
    client.force_login(staff_user)

    response = client.get(reverse("opengraph_preview"))

    assert b"img/open_graph.png" in response.content


def test_it_survives_an_empty_database(client, staff_user):
    """Nothing to preview should still render, not blow up."""
    client.force_login(staff_user)

    response = client.get(reverse("opengraph_preview"))

    assert response.status_code == 200
    assert b"to preview" in response.content


def test_a_local_host_explains_why_there_is_no_image(client, staff_user, package):
    """The renderer cannot reach localhost, so the page says so."""
    client.force_login(staff_user)

    response = client.get(reverse("opengraph_preview"), SERVER_NAME="localhost")

    assert b"cannot reach this host" in response.content
    assert b"v1.screenshot.11ty.dev" in response.content  # the link is still there


def test_a_public_host_shows_the_rendered_image(client, staff_user, package):
    client.force_login(staff_user)

    response = client.get(reverse("opengraph_preview"), SERVER_NAME="djangopackages.org")
    content = response.content.decode()

    assert '<img src="https://v1.screenshot.11ty.dev/' in content
    assert "cannot reach this host" not in content
