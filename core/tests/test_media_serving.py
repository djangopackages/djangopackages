"""Uploaded files are served from MEDIA_ROOT with DEBUG off, which is how production runs."""

import pytest
from django.test import override_settings


@pytest.mark.django_db
def test_media_is_served_with_debug_off(client, settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    (tmp_path / "blog").mkdir()
    (tmp_path / "blog" / "cat.png").write_bytes(b"\x89PNG not really")

    with override_settings(DEBUG=False):
        response = client.get("/media/blog/cat.png")

    assert response.status_code == 200
    assert b"".join(response.streaming_content) == b"\x89PNG not really"


@pytest.mark.django_db
def test_missing_media_is_a_404(client, settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path

    with override_settings(DEBUG=False):
        assert client.get("/media/blog/nope.png").status_code == 404
