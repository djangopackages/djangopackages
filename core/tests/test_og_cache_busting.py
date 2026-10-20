"""The renderer caches by target URL, so we need a key we control."""

import pytest
from django.urls import reverse

pytestmark = pytest.mark.django_db


def og_image(response):
    import re

    match = re.search(
        r'<meta property="og:image" content="([^"]+)"', response.content.decode()
    )
    return match.group(1) if match else ""


def test_the_card_url_carries_the_version(client, settings):
    settings.OG_IMAGE_VERSION = "7"

    image = og_image(client.get(reverse("home")))

    assert "%3Fv%3D7" in image


def test_bumping_the_version_changes_the_image_url(client, settings):
    """A bump has to reach the renderer, or a bad render sticks."""
    settings.OG_IMAGE_VERSION = "1"
    first = og_image(client.get(reverse("home")))

    settings.OG_IMAGE_VERSION = "2"
    second = og_image(client.get(reverse("home")))

    assert first != second


def test_the_dead_cache_buster_segment_is_gone(client):
    """_20230219 looked like a cache buster but the renderer ignored it."""
    assert "_20230219" not in og_image(client.get(reverse("home")))


def test_the_fallback_image_is_left_alone(client):
    """The static card is served by us, so it needs no version."""
    response = client.get(reverse("faq"))

    image = og_image(response)
    assert image.endswith("img/open_graph.png")
    assert "?v=" not in image
