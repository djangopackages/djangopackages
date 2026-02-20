from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from banners.cache import invalidate_banner_cache
from banners.models import Banner


@receiver(post_save, sender=Banner)
def banner_post_save(sender, **kwargs):
    """Invalidate banner cache whenever a banner is saved."""
    invalidate_banner_cache()


@receiver(post_delete, sender=Banner)
def banner_post_delete(sender, **kwargs):
    """Invalidate banner cache whenever a banner is deleted."""
    invalidate_banner_cache()
