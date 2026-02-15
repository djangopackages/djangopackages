from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVectorField
from django.db import models
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from core.models import BaseModel
from searchv3.search import SearchV3QuerySet, build_search_vector


class ItemType(models.TextChoices):
    PACKAGE = "package", _("Package")
    GRID = "grid", _("Grid")


class SearchV3(BaseModel):
    """Denormalized search index with PostgreSQL full-text search support."""

    weight = models.IntegerField(_("Weight"), default=0)
    item_type = models.CharField(
        _("Item Type"),
        max_length=40,
        choices=ItemType,
    )
    title = models.CharField(_("Title"), max_length=100, db_index=True)
    slug = models.SlugField(_("Slug"), db_index=True)
    description = models.TextField(_("Repo Description"), blank=True)
    category = models.CharField(_("Category"), blank=True, max_length=50)
    repo_watchers = models.IntegerField(_("Stars"), default=0)
    repo_forks = models.IntegerField(_("repo forks"), default=0)
    pypi_downloads = models.IntegerField(_("PyPI downloads"), default=0)
    score = models.IntegerField(_("Score"), default=0)
    search_vector = models.GeneratedField(
        expression=build_search_vector(),
        output_field=SearchVectorField(),
        db_persist=True,
    )
    usage = models.IntegerField(_("Number of users"), default=0)
    participants = models.TextField(
        _("Participants"),
        help_text="List of collaborators/participants on the project",
        blank=True,
    )
    last_committed = models.DateTimeField(_("Last commit"), blank=True, null=True)
    last_released = models.DateTimeField(_("Last release"), blank=True, null=True)

    objects = SearchV3QuerySet.as_manager()

    class Meta:
        ordering = ["-weight"]
        verbose_name_plural = "SearchV3s"
        indexes = [
            models.Index(fields=["item_type", "slug"], name="searchv3_item_slug"),
            GinIndex(fields=["search_vector"], name="searchv3_vec_gin"),
            GinIndex(
                fields=["title"],
                name="searchv3_title_trgm",
                opclasses=["gin_trgm_ops"],
            ),
            GinIndex(
                fields=["slug"],
                name="searchv3_slug_trgm",
                opclasses=["gin_trgm_ops"],
            ),
        ]

    def __str__(self):
        return f"{self.item_type}: {self.title} - {self.slug}"

    def get_absolute_url(self):
        """Generate the absolute URL based on item_type and slug."""
        if self.item_type == ItemType.PACKAGE:
            return reverse_lazy("package", kwargs={"slug": self.slug})
        elif self.item_type == ItemType.GRID:
            return reverse_lazy("grid", kwargs={"slug": self.slug})
        return ""

    @property
    def is_grid(self) -> bool:
        return self.item_type == ItemType.GRID
