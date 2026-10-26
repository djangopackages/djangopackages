"""Staff can preview a draft or scheduled post at its public URL; nobody else can. See #1799."""

from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from model_bakery import baker

pytestmark = pytest.mark.django_db


def make_post(**kwargs):
    kwargs.setdefault("title", "A draft")
    kwargs.setdefault("content", "Not yet.")
    return baker.make("blog.Post", **kwargs)


@pytest.fixture()
def draft():
    return make_post(slug="a-draft", status="draft")


@pytest.fixture()
def scheduled():
    return make_post(
        slug="a-scheduled-post",
        status="published",
        published_date=timezone.now() + timedelta(days=1),
    )


@pytest.fixture()
def published():
    return make_post(
        slug="a-release",
        status="published",
        published_date=timezone.now() - timedelta(days=1),
    )


@pytest.fixture()
def staff(client):
    user = get_user_model().objects.create_user("staff", password="x", is_staff=True)
    client.force_login(user)
    return user


@pytest.fixture()
def member(client):
    user = get_user_model().objects.create_user("member", password="x")
    client.force_login(user)
    return user


def url(post):
    return reverse("post_detail", args=[post.slug])


def test_staff_sees_a_draft_with_the_banner(client, staff, draft):
    response = client.get(url(draft))

    assert response.status_code == 200
    assert response.context["is_preview"] is True
    assert (
        "This post is a draft and is not visible to the public"
        in response.content.decode()
    )
    assert (
        reverse("admin:blog_post_change", args=[draft.pk]) in response.content.decode()
    )


def test_staff_sees_a_scheduled_post_with_its_date(client, staff, scheduled):
    response = client.get(url(scheduled))

    assert response.status_code == 200
    assert "is scheduled for" in response.content.decode()
    assert "not visible to the public yet" in response.content.decode()


def test_a_published_post_has_no_banner(client, staff, published):
    response = client.get(url(published))

    assert response.status_code == 200
    assert response.context["is_preview"] is False
    assert "Preview." not in response.content.decode()


def test_anonymous_gets_a_404_for_a_draft(client, draft, scheduled):
    assert client.get(url(draft)).status_code == 404
    assert client.get(url(scheduled)).status_code == 404


def test_a_logged_in_non_staff_user_gets_a_404_too(client, member, draft):
    assert client.get(url(draft)).status_code == 404


def test_drafts_stay_out_of_the_list_for_staff(client, staff, draft, published):
    response = client.get(reverse("post_list"))

    assert list(response.context["posts"]) == [published]


def test_a_draft_gets_a_slug_on_save_so_it_has_a_url():
    post = make_post(title="Coming Soon", slug=None)

    assert post.slug == "coming-soon"
    assert post.get_absolute_url() == "/changelog/coming-soon/"


def test_a_post_published_on_first_save_keeps_the_dated_slug():
    post = make_post(
        title="Shipped", slug=None, status="published", published_date=timezone.now()
    )

    assert post.slug == f"{timezone.now():%Y-%m-%d}-shipped"


def test_is_public(draft, scheduled, published):
    assert not draft.is_public
    assert not scheduled.is_public
    assert published.is_public
