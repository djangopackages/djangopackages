from urllib.parse import quote_plus

from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse
from django.views.generic import TemplateView
from health_check.views import HealthCheckView as BaseHealthCheckView
from redis.asyncio import Redis as RedisClient

from blog.models import Post
from grid.models import Grid
from package.models import Category, Package
from products.models import Release
from profiles.models import Profile


class HealthCheckView(BaseHealthCheckView):
    """Health checks, with Redis included only when REDIS_URL is set.

    The checks are built per request, so they follow the current settings
    rather than whatever REDIS_URL was when urls.py was first imported.
    """

    def get_checks(self):
        checks = [
            "health_check.Cache",
            "health_check.Database",
        ]
        if settings.REDIS_URL:
            checks.append(
                (
                    "health_check.contrib.redis.Redis",
                    {
                        "client_factory": lambda: RedisClient.from_url(
                            settings.REDIS_URL
                        )
                    },
                )
            )
        self.checks = checks
        return super().get_checks()


class OpenGraphPreviewView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """Staff-only gallery of every social card we render.

    Unlisted and noindex on purpose. It exists so a card design change can be
    eyeballed across all three types without sharing links on social media and
    waiting for a crawler to catch up.
    """

    template_name = "core/opengraph_preview.html"

    def test_func(self):
        return self.request.user.is_staff

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        def pick(queryset, *, prefer):
            """A filled-in example if there is one, otherwise anything."""
            return queryset.filter(**prefer).first() or queryset.first()

        package = pick(
            Package.objects.order_by("-score", "title"),
            prefer={"repo_description__gt": ""},
        )
        grid = pick(
            Grid.objects.approved().order_by("title"),
            prefer={"description__gt": ""},
        )
        profile = pick(
            Profile.objects.order_by("-user__date_joined"),
            prefer={"github_account__gt": ""},
        )
        post = Post.objects.published().first()
        category = Category.objects.order_by("title").first()
        release = Release.objects.select_related("product").order_by("-release").first()

        base_url = f"{self.request.scheme}://{self.request.get_host()}"

        def card(label, card_path, page_url):
            return {
                "label": label,
                "card_path": card_path,
                "page_url": page_url,
                "proxy_url": (
                    "https://v1.screenshot.11ty.dev/"
                    f"{quote_plus(base_url + card_path)}/opengraph/_20230219/"
                ),
            }

        cards = [
            card(
                "Homepage",
                reverse("home_opengraph"),
                reverse("home"),
            ),
        ]

        # The cards that need a row in the database to render.
        for label, obj in (
            ("Package", package),
            ("Grid", grid),
            ("Profile", profile),
            ("Changelog post", post),
            ("Category", category),
        ):
            if obj is None:
                cards.append({"label": label})
                continue
            cards.append(
                card(label, obj.get_opengraph_image_url(), obj.get_absolute_url())
            )

        if release is None:
            cards.append({"label": "Readiness detail"})
        else:
            args = [release.product.slug, release.cycle]
            cards.append(
                card(
                    "Readiness detail",
                    reverse("readiness_detail_opengraph", args=args),
                    reverse("readiness_detail", args=args),
                )
            )

        for label, card_name, page_name in (
            ("Packages", "packages_opengraph", "packages"),
            ("Grids", "grids_opengraph", "grids"),
            ("Readiness", "readiness_opengraph", "readiness"),
            ("Open", "open_opengraph", "open"),
        ):
            cards.append(card(label, reverse(card_name), reverse(page_name)))

        context["cards"] = cards
        context["fallback_url"] = f"{base_url}{settings.STATIC_URL}img/open_graph.png"
        # The renderer fetches the card over the public internet, so it cannot
        # reach a development host. Say so rather than show a broken image.
        context["host_is_reachable"] = not any(
            self.request.get_host().startswith(prefix)
            for prefix in ("localhost", "127.0.0.1", "0.0.0.0", "[::1]")
        )
        # Everything public has a card now. What is left is the pages where
        # the fallback is the right answer.
        context["fallback_pages"] = [
            (
                "Changelog index",
                "/changelog/",
                "A list of posts, not a thing to share.",
            ),
            ("Colophon", "/colophon/", "Static page."),
            ("FAQ", "/faq/", "Static page."),
            ("Search results", "/search/", "Query specific, and noindex anyway."),
            ("Forms and error pages", "", "Nothing to put on a card."),
        ]
        return context


class OpenGraphCardView(TemplateView):
    """A social card for a page with no model behind it.

    Configured straight from urls.py with as_view(), so a page that just
    needs a kind, a heading and a blurb does not need its own class.
    """

    template_name = "partials/opengraph_card.html"
    card_kind = ""
    card_title = ""
    card_description = ""
    url_name = ""

    def get_card_path(self):
        return reverse(self.url_name)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            card_kind=self.card_kind,
            card_title=self.card_title,
            card_description=self.card_description,
            card_path=self.get_card_path(),
        )
        return context
