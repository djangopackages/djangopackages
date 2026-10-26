"""Authors upload an image, then embed it in a post's Markdown content."""

import io

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from model_bakery import baker
from PIL import Image

from blog.models import PostImage

pytestmark = pytest.mark.django_db


def a_png():
    buf = io.BytesIO()
    Image.new("RGB", (1, 1)).save(buf, format="PNG")
    return SimpleUploadedFile("x.png", buf.getvalue(), content_type="image/png")


def test_uploaded_image_gives_a_pasteable_markdown_snippet(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path

    img = PostImage(image=a_png())
    img.save()

    url = img.image.url  # ty: ignore[unresolved-attribute] — FieldFile has .url
    assert url.startswith("/media/blog/")
    assert img.markdown == f"![]({url})"


def test_content_image_renders_as_an_img_tag(client):
    """The whole point: a URL pasted into the body becomes an <img>."""
    post = baker.make(
        "blog.Post",
        slug="with-image",
        content="![a cat](/media/blog/cat.png)",
        published_date="2020-01-01T00:00:00Z",
        status="published",
    )

    content = client.get(reverse("post_detail", args=[post.slug])).content.decode()

    assert '<img src="/media/blog/cat.png"' in content
    assert 'alt="a cat"' in content
