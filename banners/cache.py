from django.conf import settings
from django.core.cache import cache
from banners.models import Banner

BANNER_CACHE_KEY = "banners:active_banner"

# A sentinel distinct from None so we can cache a "no banner" result.
# cache.get() returns None by default when a key is missing, which would be
# indistinguishable from a cached "no active banner" (None).  Using a private
# sentinel lets us tell the difference: _CACHE_MISS means "not in cache yet",
# None means "cache says there is no active banner right now".
_CACHE_MISS = object()


def get_active_banner():
    """Return the active banner, using cache when available."""
    banner = cache.get(BANNER_CACHE_KEY, _CACHE_MISS)

    if banner is _CACHE_MISS:
        banner = Banner.objects.active().first()
        cache.set(BANNER_CACHE_KEY, banner, timeout=settings.CACHE_TIMEOUT)

    return banner


def invalidate_banner_cache():
    """Delete the cached active banner."""
    cache.delete(BANNER_CACHE_KEY)
