from banners.cache import get_active_banner


def active_banner(request):
    """Add the current active banner to the template context.

    Skips banners that the user has already dismissed (stored in their session).
    """
    banner = get_active_banner()
    if banner and (session := getattr(request, "session", {})):
        if session.get(f"dismissed_banner_{banner.pk}"):
            banner = None
    return {"active_banner": banner}
