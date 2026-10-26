"""A post is public only when it's published and its publish date has arrived."""

from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone
from model_bakery import baker

pytestmark = pytest.mark.django_db


def make_post(**kwargs):
    kwargs.setdefault("title", "A release")
    kwargs.setdefault("slug", "a-release")
    kwargs.setdefault("content", "We shipped a thing.")
    return baker.make("blog.Post", **kwargs)


@pytest.fixture()
def published():
    return make_post(
        status="published",
        published_date=timezone.now() - timedelta(days=1),
    )


@pytest.fixture()
def draft():
    return make_post(
        slug="a-draft",
        status="draft",
        published_date=timezone.now() - timedelta(days=1),
    )


@pytest.fixture()
def scheduled():
    """Published, but the publish date is in the future."""
    return make_post(
        slug="a-scheduled-post",
        status="published",
        published_date=timezone.now() + timedelta(days=1),
    )


class TestDetail:
    def test_published_post_shows(self, client, published):
        response = client.get(reverse("post_detail", args=[published.slug]))
        assert response.status_code == 200

    def test_draft_post_is_a_404(self, client, draft):
        response = client.get(reverse("post_detail", args=[draft.slug]))
        assert response.status_code == 404

    def test_scheduled_post_is_a_404_until_its_date(self, client, scheduled):
        response = client.get(reverse("post_detail", args=[scheduled.slug]))
        assert response.status_code == 404


class TestList:
    def test_only_published_posts_appear(self, client, published, draft, scheduled):
        response = client.get(reverse("post_list"))
        posts = list(response.context["posts"])
        assert posts == [published]


class TestFeed:
    def test_only_published_posts_appear(self, client, published, draft, scheduled):
        content = client.get(reverse("post_feed")).content.decode()
        assert published.title in content
        assert "a-draft" not in content
        assert "a-scheduled-post" not in content


class TestManager:
    def test_published_excludes_draft_and_scheduled(self, published, draft, scheduled):
        from blog.models import Post

        assert list(Post.objects.published()) == [published]
