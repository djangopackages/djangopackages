import django.dispatch
from django.db import transaction
from django.db.models.signals import m2m_changed, post_save, pre_delete
from django.dispatch import receiver
from django_q.tasks import async_task

# Custom signal for fetching package metadata
signal_fetch_latest_metadata = django.dispatch.Signal()


@receiver(post_save, sender="package.Package")
def on_package_save(sender, instance, created, **kwargs):
    """
    Invalidate related grid caches when a package is saved.
    """
    package_id = instance.pk

    if not package_id:
        return

    transaction.on_commit(
        lambda pid=package_id: async_task(
            "grid.tasks.invalidate_grids_for_package_task", pid
        )
    )


@receiver(pre_delete, sender="package.Package")
def on_package_pre_delete(sender, instance, **kwargs):
    """
    Invalidate related grid caches when a package is deleted.

    Uses pre_delete to capture related grids before CASCADE deletes remove the
    GridPackage rows.
    """
    from grid.models import GridPackage

    grid_ids = [
        gid
        for gid in GridPackage.objects.filter(package_id=instance.pk).values_list(
            "grid_id", flat=True
        )
    ]

    if not grid_ids:
        return

    transaction.on_commit(
        lambda gids=grid_ids: async_task(
            "grid.tasks.invalidate_multiple_grids_cache_task", gids
        )
    )


@receiver(m2m_changed, sender="package.Package_usage")
def on_package_usage_changed(sender, instance, action, **kwargs):
    """
    Invalidate grid caches when usage (users using package) changes.
    """
    if action in ("post_add", "post_remove", "post_clear"):
        package_id = instance.pk

        if not package_id:
            return

        transaction.on_commit(
            lambda pid=package_id: async_task(
                "grid.tasks.invalidate_grids_for_package_task", pid
            )
        )
