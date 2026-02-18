import hashlib
import logging
from collections.abc import Iterable
from typing import Any

from django.core.cache import cache

logger = logging.getLogger(__name__)

GRID_DETAIL_PAYLOAD_TIMEOUT = 60 * 60  # 1 hour
_GRID_DETAIL_VERSION_DEFAULT = 1


def _version_key(grid_id: int) -> str:
    return f"grid.detail.v:{grid_id}"


def get_grid_detail_cache_version(grid_id: int) -> int:
    key = _version_key(grid_id)
    version = cache.get(key)

    if isinstance(version, int) and version >= _GRID_DETAIL_VERSION_DEFAULT:
        return version

    try:
        normalized = int(version)
    except (TypeError, ValueError):
        normalized = _GRID_DETAIL_VERSION_DEFAULT

    if normalized < _GRID_DETAIL_VERSION_DEFAULT:
        normalized = _GRID_DETAIL_VERSION_DEFAULT

    # If we found garbage (or nothing), write back a sane int to keep future
    # reads fast and to make cache.incr more likely to succeed.
    if version != normalized:
        cache.set(key, normalized, None)
    return normalized


def bump_grid_detail_cache_version(grid_id: int) -> None:
    key = _version_key(grid_id)
    try:
        cache.incr(key)
        return
    except Exception:
        pass

    cache.set(key, get_grid_detail_cache_version(grid_id) + 1, None)


def _normalized_filter_data_key(filter_data: dict[str, Any] | None) -> str:
    """Return a compact, stable representation of public filter controls.

    This is intentionally string-based (not JSON) to avoid serialization
    overhead on a hot path.
    """
    filter_data = filter_data or {}
    stable = "1" if filter_data.get("stable") else "0"
    sort = filter_data.get("sort", "")
    q = str(filter_data.get("q", "")).strip().lower()
    return f"s={stable}&o={sort}&q={q}"


def get_grid_detail_payload_cache_key(
    *,
    grid_id: int,
    language: str = "",
    filter_data: dict[str, Any] | None = None,
    max_packages: int = 10,
    show_features: bool = True,
) -> str:
    """Cache key for the heavy "comparison payload" within the grid detail view.

    The key includes:
    - grid_id
    - per-grid cache version (so invalidation is a single bump)
    - active language
    - normalized filter_data (hashed)
    - max_packages (affects slicing)
    - show_features (whether grid features are displayed)
    """
    version = get_grid_detail_cache_version(grid_id)
    lang = language or ""
    feat = "1" if show_features else "0"
    normalized = _normalized_filter_data_key(filter_data)
    digest = hashlib.blake2s(normalized.encode("utf-8"), digest_size=8).hexdigest()
    return (
        f"grid.detail.payload:{grid_id}:{version}:{lang}:{max_packages}:{feat}:{digest}"
    )


def invalidate_grid_cache(grid_id: int) -> None:
    """Invalidate cached grid detail responses."""
    bump_grid_detail_cache_version(grid_id)


def invalidate_cache_for_grids(grid_ids: Iterable[int]) -> None:
    """
    Invalidate cache for multiple grids.

    Args:
        grid_ids: Iterable of grid primary keys
    """
    for grid_id in grid_ids:
        invalidate_grid_cache(grid_id)


def invalidate_grids_for_package(package_id: int) -> None:
    """
    Invalidate all grid caches that contain a specific package.

    Args:
        package_id: The package's primary key
    """
    from grid.models import GridPackage

    grid_ids = list(
        GridPackage.objects.filter(package_id=package_id)
        .values_list("grid_id", flat=True)
        .distinct()
    )

    if grid_ids:
        invalidate_cache_for_grids(grid_ids)
        logger.debug(
            f"Invalidated {len(grid_ids)} grid caches for package {package_id}"
        )
