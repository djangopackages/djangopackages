from django.db import transaction
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django_q.tasks import async_task


@receiver(post_save, sender="grid.Grid")
def on_grid_save(sender, instance, created, **kwargs):
    """
    Invalidate grid cache when a grid is saved.
    """
    grid_id = instance.pk

    if not grid_id:
        return

    transaction.on_commit(
        lambda gid=grid_id: async_task("grid.tasks.invalidate_grid_cache_task", gid)
    )


@receiver([post_save, post_delete], sender="grid.GridPackage")
def on_grid_package_change(sender, instance, **kwargs):
    """
    Invalidate grid cache when a package is added/removed from a grid.
    """
    grid_id = instance.grid_id

    if not grid_id:
        return

    transaction.on_commit(
        lambda gid=grid_id: async_task("grid.tasks.invalidate_grid_cache_task", gid)
    )


@receiver([post_save, post_delete], sender="grid.Feature")
def on_feature_change(sender, instance, **kwargs):
    """
    Invalidate grid cache when a feature is created, updated, or deleted.
    """
    grid_id = instance.grid_id

    if not grid_id:
        return

    transaction.on_commit(
        lambda gid=grid_id: async_task("grid.tasks.invalidate_grid_cache_task", gid)
    )


@receiver([post_save, post_delete], sender="grid.Element")
def on_element_change(sender, instance, **kwargs):
    """
    Invalidate grid cache when an element is created, updated, or deleted.
    """
    # Element -> GridPackage -> Grid
    grid_package = instance.grid_package

    if not grid_package:
        return

    grid_id = grid_package.grid_id

    if not grid_id:
        return

    transaction.on_commit(
        lambda gid=grid_id: async_task("grid.tasks.invalidate_grid_cache_task", gid)
    )
