from django.conf import settings
from django.core.cache import cache
from banners.models import Banner

BANNER_CACHE_KEY = "banners:active_banners"

# A sentinel distinct from None so we can cache a "no banners" result.
# cache.get() returns None by default when a key is missing, which would be
# indistinguishable from a cached "no active banners" (None).  Using a private
# sentinel lets us tell the difference: _CACHE_MISS means "not in cache yet",
# None means "cache says there are no active banners right now".
_CACHE_MISS = object()


def get_active_banners():
    """Return all active banners, using cache when available."""
    banners = cache.get(BANNER_CACHE_KEY, _CACHE_MISS)

    if banners is _CACHE_MISS:
        banners = list(Banner.objects.active())
        cache.set(BANNER_CACHE_KEY, banners, timeout=settings.CACHE_TIMEOUT)

    return banners


def invalidate_banner_cache():
    """Delete the cached active banners."""
    cache.delete(BANNER_CACHE_KEY)
