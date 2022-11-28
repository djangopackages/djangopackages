from django import template
from django.conf import settings
from django.utils.translation import gettext_lazy as _

register = template.Library()


@register.inclusion_tag("includes/page_metadata.html", takes_context=True)
def page_metadata(context, page_title=None, page_description=None, page_keywords=None):
    request = context["request"]
    site_title = getattr(settings, "SITE_TITLE", "Django Packages")
    base_url = f"{request.scheme}://{request.get_host()}"
    page_title = page_title or _("Reusable apps, sites and tools directory for Django")
    page_keywords = page_keywords or _(
        "Django, Django Apps, Packages, Tools, Django Sites, Django Resources"
    )
    page_description = page_description or _(
        "Django Packages stores information on fetched packages "
        "and provides easy comparison tools for them. "
        "Public APIs include PyPI, Github, and BitBucket."
    )
    return {
        "site_title": site_title,
        "base_url": base_url,
        "static_url": settings.STATIC_URL,
        "page_url": f"{base_url}{request.path}",
        "page_title": page_title,
        "page_description": page_description,
        "page_keywords": page_keywords,
    }
