"""Every public page should name a card, and every card should render."""

import re
from urllib.parse import quote_plus

import pytest
from django.urls import reverse
from model_bakery import baker

pytestmark = pytest.mark.django_db


def og_image(response):
    match = re.search(
        r'<meta property="og:image" content="([^"]+)"', response.content.decode()
    )
    return match.group(1) if match else ""


SITE_CARDS = [
    ("home", "home_opengraph"),
    ("packages", "packages_opengraph"),
    ("grids", "grids_opengraph"),
    ("open", "open_opengraph"),
    ("readiness", "readiness_opengraph"),
]


@pytest.mark.parametrize("page_name,card_name", SITE_CARDS)
def test_a_site_page_points_at_its_own_card(client, page_name, card_name):
    response = client.get(reverse(page_name))

    assert quote_plus(reverse(card_name)) in og_image(response)


@pytest.mark.parametrize("page_name,card_name", SITE_CARDS)
def test_a_site_card_renders(client, page_name, card_name):
    response = client.get(reverse(card_name))

    assert response.status_code == 200
    assert b"Django Packages" in response.content


def test_a_site_page_does_not_use_the_fallback_image(client):
    """The whole point: these used to get the generic logo."""
    for page_name, _ in SITE_CARDS:
        assert "img/open_graph.png" not in og_image(client.get(reverse(page_name)))


def test_the_homepage_card_has_no_badge(client):
    """The badge would just repeat the footer."""
    content = client.get(reverse("home_opengraph")).content.decode()

    assert "rounded-full border-2" not in content


class TestCategoryCard:
    def test_the_page_points_at_the_card(self, client):
        category = baker.make("package.Category", slug="apps", title="App")

        response = client.get(category.get_absolute_url())

        assert quote_plus(category.get_opengraph_image_url()) in og_image(response)

    def test_the_card_shows_the_category(self, client):
        category = baker.make(
            "package.Category",
            slug="apps",
            title="App",
            title_plural="Apps",
            description="Small components.",
        )

        response = client.get(category.get_opengraph_image_url())
        content = response.content.decode()

        assert "Apps" in content
        assert "Small components." in content
        assert "Category" in content


class TestChangelogCard:
    @pytest.fixture()
    def post(self):
        return baker.make(
            "blog.Post",
            title="A release",
            slug="a-release",
            content="We shipped a thing. " * 30,
            published_date="2026-01-01T00:00:00Z",
        )

    def test_the_page_points_at_the_card(self, client, post):
        response = client.get(post.get_absolute_url())

        assert quote_plus(post.get_opengraph_image_url()) in og_image(response)

    def test_the_card_shows_the_post(self, client, post):
        response = client.get(post.get_opengraph_image_url())
        content = response.content.decode()

        assert "A release" in content
        assert "Changelog" in content

    def test_the_summary_is_trimmed(self, post):
        """A whole post will not fit on a card."""
        assert len(post.summary) <= 180
        assert post.summary.startswith("We shipped a thing.")


class TestReadinessDetailCard:
    @pytest.fixture()
    def release(self):
        product = baker.make("products.Product", slug="django", title="Django")
        return baker.make("products.Release", product=product, cycle="6.0")

    def test_the_card_names_the_release(self, client, release):
        response = client.get(
            reverse("readiness_detail_opengraph", args=["django", "6.0"])
        )

        assert response.status_code == 200
        assert b"Django 6.0 readiness" in response.content

    def test_an_unknown_release_is_a_404(self, client, release):
        response = client.get(
            reverse("readiness_detail_opengraph", args=["django", "99.9"])
        )

        assert response.status_code == 404


class TestSharedChrome:
    """The frame every card has in common."""

    def test_a_card_is_the_right_size(self, client):
        content = client.get(reverse("home_opengraph")).content.decode()

        assert "h-[630px] w-[1200px]" in content

    def test_the_footer_cannot_be_pushed_off(self, client):
        """A two line heading used to grow the card past 630px."""
        content = client.get(reverse("home_opengraph")).content.decode()

        assert "overflow-hidden" in content
        assert "min-h-0 flex-1" in content

    def test_no_card_advertises_a_domain_we_do_not_own(self, client, grid):
        """djangogrids.org has no DNS record at all."""
        for name in ("home_opengraph", "packages_opengraph", "grids_opengraph"):
            assert b"djangogrids.org" not in client.get(reverse(name)).content
