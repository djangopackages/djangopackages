from banners.cache import get_active_banners


def active_banner(request):
    """Add active banners to the template context, excluding dismissed ones."""
    banners = get_active_banners()
    if banners and (session := getattr(request, "session", {})):
        banners = [b for b in banners if not session.get(f"dismissed_banner_{b.pk}")]
    return {"active_banners": banners}
