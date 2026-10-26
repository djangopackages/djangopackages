from django.conf import settings

from core import __version__


def core_values(request):
    """
    A nice pun. But this is how we stick handy data everywhere.

    """
    data = {
        "FRAMEWORK_TITLE": getattr(settings, "FRAMEWORK_TITLE", "Django"),
        "SITE_TITLE": getattr(settings, "SITE_TITLE", "Django Packages"),
        # The deployed version, for the footer. Bumped by the release
        # workflow in core/__init__.py.
        "VERSION": __version__,
    }
    return data
