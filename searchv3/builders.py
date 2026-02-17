from __future__ import annotations

from abc import ABC, abstractmethod

from django.db.models import Count, Exists, OuterRef, QuerySet
from rich import print

from grid.models import Grid
from package.models import Package
from searchv2.rules import (
    DeprecatedRule,
    DescriptionRule,
    DownloadsRule,
    ForkRule,
    LastUpdatedRule,
    RecentReleaseRule,
    UsageCountRule,
    WatchersRule,
    calc_package_weight,
)

from searchv3.models import ItemType, SearchV3


class SearchIndexBuilder(ABC):
    """Abstract base for indexing source models into SearchV3."""

    item_type: ItemType

    @abstractmethod
    def get_queryset(self) -> QuerySet: ...

    @abstractmethod
    def calc_weight(self, instance) -> int: ...

    @abstractmethod
    def get_defaults(self, instance) -> dict: ...

    def build(self, *, verbose: bool = False, batch_size: int = 500) -> int:
        """Index all items using batched upserts. Returns count of indexed items."""
        count = 0
        batch = []

        for instance in self.get_queryset().iterator(chunk_size=batch_size):
            batch.append(instance)
            if len(batch) >= batch_size:
                count += self._upsert_batch(batch=batch, verbose=verbose)
                batch = []

        if batch:
            count += self._upsert_batch(batch=batch, verbose=verbose)

        return count

    def _upsert_batch(self, *, batch: list, verbose: bool = False) -> int:
        payload_by_slug = {}
        for instance in batch:
            try:
                weight = self.calc_weight(instance)
                defaults = self.get_defaults(instance)
                defaults["weight"] = weight
                payload_by_slug[instance.slug] = defaults
                if verbose:
                    print(f"{instance.pk=}::{weight=}")
            except Exception as e:
                print(f"[red]{e=}[/red]")

        if not payload_by_slug:
            return 0

        slugs = list(payload_by_slug.keys())
        existing = SearchV3.objects.filter(
            item_type=self.item_type,
            slug__in=slugs,
        )
        existing_by_slug = {obj.slug: obj for obj in existing}

        fields = list(next(iter(payload_by_slug.values())).keys())
        to_create = []
        to_update = []

        for slug, defaults in payload_by_slug.items():
            if slug in existing_by_slug:
                obj = existing_by_slug[slug]
                for field in fields:
                    setattr(obj, field, defaults[field])
                to_update.append(obj)
            else:
                to_create.append(
                    SearchV3(item_type=self.item_type, slug=slug, **defaults)
                )

        if to_create:
            SearchV3.objects.bulk_create(to_create, batch_size=len(to_create))
        if to_update:
            SearchV3.objects.bulk_update(
                to_update, fields=fields, batch_size=len(to_update)
            )

        return len(payload_by_slug)


_PACKAGE_RULES = [
    DeprecatedRule(),
    DescriptionRule(),
    DownloadsRule(),
    ForkRule(),
    LastUpdatedRule(),
    RecentReleaseRule(),
    UsageCountRule(),
    WatchersRule(),
]


class PackageIndexBuilder(SearchIndexBuilder):
    item_type = ItemType.PACKAGE

    def get_queryset(self):
        return (
            Package.objects.select_related("category", "latest_version")
            .annotate(usage_count=Count("usage", distinct=True))
            .all()
        )

    def calc_weight(self, package: Package) -> int:
        result = calc_package_weight(
            package=package, rules=_PACKAGE_RULES, max_score=100
        )
        return result["total_score"]

    def get_defaults(self, package: Package) -> dict:
        return {
            "category": package.category.title if package.category else "",
            "description": package.repo_description or "",
            "participants": package.participants or "",
            "pypi_downloads": package.pypi_downloads,
            "repo_forks": package.repo_forks,
            "repo_watchers": package.repo_watchers,
            "score": package.score,
            "title": package.title,
            "usage": package.usage_count,
            "last_committed": package.last_commit_date,
            "last_released": (
                package.latest_version.upload_time
                if package.latest_version and package.latest_version.upload_time
                else None
            ),
        }


def calc_grid_weight(*, grid: Grid, max_weight: int = 100) -> int:
    """Score a Grid relative to the highest package weight."""
    increment = max_weight / 6
    weight = max_weight - increment

    if not grid.is_locked:
        weight -= increment

    if not grid.header:
        weight -= increment

    package_count = getattr(grid, "package_count", None)
    has_packages = (
        package_count > 0 if package_count is not None else grid.packages.exists()
    )
    if not has_packages:
        weight -= increment

    return int(weight)


class GridIndexBuilder(SearchIndexBuilder):
    item_type = ItemType.GRID

    def __init__(self, *, max_weight: int = 0):
        self._max_weight = max_weight

    def get_queryset(self):
        return Grid.objects.annotate(
            package_count=Count("packages", distinct=True)
        ).all()

    def calc_weight(self, grid: Grid) -> int:
        return calc_grid_weight(grid=grid, max_weight=self._max_weight)

    def get_defaults(self, grid: Grid) -> dict:
        return {
            "description": grid.description or "",
            "title": grid.title,
        }


def build_search_index(*, verbose: bool = False):
    """Build the full SearchV3 index.

    1. Delete stale entries whose source Package/Grid no longer exists.
    2. Index packages.
    3. Index grids (weighted relative to highest package weight).
    """
    package_score_max = 100

    package_exists = Package.objects.filter(slug=OuterRef("slug"))
    (
        SearchV3.objects.filter(item_type=ItemType.PACKAGE)
        .annotate(source_exists=Exists(package_exists))
        .filter(source_exists=False)
        .delete()
    )

    grid_exists = Grid.objects.filter(slug=OuterRef("slug"))
    (
        SearchV3.objects.filter(item_type=ItemType.GRID)
        .annotate(source_exists=Exists(grid_exists))
        .filter(source_exists=False)
        .delete()
    )

    PackageIndexBuilder().build(verbose=verbose)

    # Determine highest package weight (package rows only) with a practical
    # fallback when no packages are indexed (e.g., empty dataset).
    top_package = (
        SearchV3.objects.filter(item_type=ItemType.PACKAGE)
        .only("weight")
        .order_by("-weight")
        .first()
    )
    max_weight = top_package.weight if top_package else package_score_max

    GridIndexBuilder(max_weight=max_weight).build(verbose=verbose)
