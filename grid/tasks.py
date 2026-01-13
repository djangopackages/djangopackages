"""
Django-Q tasks for grid app cache invalidation.
"""

import logging

logger = logging.getLogger(__name__)


def invalidate_grid_cache_task(grid_id: int) -> None:
    """
    Async task to invalidate grid detail page cache.

    Args:
        grid_id: The grid's primary key
    """
    from grid.cache import invalidate_grid_cache

    logger.info(f"Invalidating grid cache for grid_id={grid_id}")
    invalidate_grid_cache(grid_id)


def invalidate_multiple_grids_cache_task(grid_ids: list[int]) -> None:
    """
    Async task to invalidate multiple grid detail page caches.

    Args:
        grid_ids: List of grid primary keys
    """
    from grid.cache import invalidate_cache_for_grids

    logger.info(f"Invalidating grid cache for grid_ids={grid_ids}")
    invalidate_cache_for_grids(grid_ids)


def invalidate_grids_for_package_task(package_id: int) -> None:
    """Async task to invalidate grid caches that include a package."""
    from grid.cache import invalidate_grids_for_package

    logger.info(
        f"Invalidating grid caches for grids containing package_id={package_id}"
    )
    invalidate_grids_for_package(package_id)
