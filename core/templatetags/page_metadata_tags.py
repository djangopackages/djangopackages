from django import template
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from urllib.parse import quote_plus

register = template.Library()


@register.inclusion_tag("includes/page_metadata.html", takes_context=True)
def page_metadata(
    context,
    page_title: str = None,
    page_description: str = None,
    page_keywords: str = None,
    og_image_url: str = None,
):
    try:
        request = context["request"]
        site_title = getattr(settings, "SITE_TITLE", "Django Packages")
        base_url = f"{request.scheme}://{request.get_host()}"
        page_title = page_title or _(
            "Reusable apps, sites and tools directory for Django"
        )
        page_keywords = page_keywords or _(
            "Django, Django Apps, Packages, Tools, Django Sites, Django Resources"
        )
        page_description = page_description or _(
            "Django Packages stores information on fetched packages "
            "and provides easy comparison tools for them. "
            "Public APIs include PyPI, GitHub, and Bitbucket."
        )

        if og_image_url is None:
            og_image_url = f"{base_url}{settings.STATIC_URL}img/open_graph.png"
        else:
            url = f"{quote_plus(base_url + og_image_url)}"
            og_image_url = f"https://v1.screenshot.11ty.dev/{url}/opengraph/_20230219/"

        return {
            "base_url": base_url,
            "og_image_url": og_image_url,
            "page_description": page_description,
            "page_keywords": page_keywords,
            "page_title": page_title,
            "page_url": f"{base_url}{request.path}",
            "site_title": site_title,
            "static_url": settings.STATIC_URL,
        }
    except KeyError:
        return {
            "site_title": getattr(settings, "SITE_TITLE", "Django Packages"),
            "static_url": settings.STATIC_URL,
        }
