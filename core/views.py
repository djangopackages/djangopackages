from urllib.parse import quote_plus

from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import TemplateView
from health_check.views import HealthCheckView as BaseHealthCheckView
from redis.asyncio import Redis as RedisClient

from grid.models import Grid
from package.models import Package
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

        base_url = f"{self.request.scheme}://{self.request.get_host()}"

        cards = []
        for label, obj, page_name in (
            ("Package", package, "package"),
            ("Grid", grid, "grid"),
            ("Profile", profile, "profile_detail"),
        ):
            if obj is None:
                cards.append({"label": label, "obj": None})
                continue

            card_path = obj.get_opengraph_image_url()
            cards.append(
                {
                    "label": label,
                    "obj": obj,
                    "card_path": card_path,
                    "page_url": obj.get_absolute_url(),
                    "proxy_url": (
                        "https://v1.screenshot.11ty.dev/"
                        f"{quote_plus(base_url + card_path)}/opengraph/_20230219/"
                    ),
                }
            )

        context["cards"] = cards
        context["fallback_url"] = f"{base_url}{settings.STATIC_URL}img/open_graph.png"
        # The renderer fetches the card over the public internet, so it cannot
        # reach a development host. Say so rather than show a broken image.
        context["host_is_reachable"] = not any(
            self.request.get_host().startswith(prefix)
            for prefix in ("localhost", "127.0.0.1", "0.0.0.0", "[::1]")
        )
        # Public pages worth their own card that still fall back, from the
        # #1468 audit. Forms, error pages and legal pages are left out: the
        # fallback is the right answer for those.
        context["fallback_pages"] = [
            (
                "Homepage",
                "/",
                "The most shared URL we have, and it has no metadata block at all.",
            ),
            (
                "Readiness",
                "/readiness/",
                'Very shareable, and the title is a hardcoded "Readiness".',
            ),
            (
                "Changelog post",
                "/changelog/",
                "Has a title and body, gets neither a description nor a card.",
            ),
            (
                "Category",
                "/categories/",
                "Categories have descriptions we never pass through.",
            ),
            ("Packages", "/packages/", "Landing page, title only."),
            ("Grids", "/grids/", "Landing page, title only."),
            ("Open", "/open/", "Stats page, title only."),
        ]
        return context
