"""The footer links the site's Mastodon account with rel="me", so Fosstodon can verify it."""

import pytest
from django.urls import reverse


@pytest.mark.django_db
def test_footer_links_mastodon_with_rel_me(client):
    html = client.get(reverse("home")).content.decode()

    assert 'href="https://fosstodon.org/@djangopackages"' in html
    assert 'rel="me"' in html


@pytest.mark.django_db
def test_footer_shows_the_deployed_version(client):
    from core import __version__

    html = client.get(reverse("home")).content.decode()

    assert f"Django Packages v{__version__}" in html
