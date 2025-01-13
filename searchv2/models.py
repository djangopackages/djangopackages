from django.core.cache import cache
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from core.models import BaseModel
from package.models import Package

ITEM_TYPE_CHOICES = (
    ("package", "Package"),
    ("grid", "Grid"),
)


class SearchV2(BaseModel):
    """
    Searches available on:

        title
        description
        grids
        packages
        categories
        stars
        number of forks
        last repo commit
        last release on PyPI
        score
    """

    weight = models.IntegerField(_("Weight"), default=0)
    item_type = models.CharField(
        _("Item Type"), max_length=40, choices=ITEM_TYPE_CHOICES
    )
    title = models.CharField(_("Title"), max_length=100, db_index=True)
    title_no_prefix = models.CharField(
        _("No Prefix Title"), max_length=100, db_index=True
    )
    slug = models.SlugField(_("Slug"), db_index=True)
    slug_no_prefix = models.SlugField(_("No Prefix Slug"), db_index=True)
    clean_title = models.CharField(
        _("Clean title with no crud"), max_length=100, db_index=True
    )
    description = models.TextField(_("Repo Description"), blank=True)
    category = models.CharField(_("Category"), blank=True, max_length=50)
    absolute_url = models.CharField(_("Absolute URL"), max_length=255)
    repo_watchers = models.IntegerField(_("Stars"), default=0)
    repo_forks = models.IntegerField(_("repo forks"), default=0)
    pypi_downloads = models.IntegerField(_("PyPI downloads"), default=0)
    score = models.IntegerField(_("Score"), default=0)
    usage = models.IntegerField(_("Number of users"), default=0)
    participants = models.TextField(
        _("Participants"),
        help_text="List of collaborats/participants on the project",
        blank=True,
    )
    last_committed = models.DateTimeField(_("Last commit"), blank=True, null=True)
    last_released = models.DateTimeField(_("Last release"), blank=True, null=True)

    class Meta:
        ordering = [
            "-weight",
        ]
        verbose_name_plural = "SearchV2s"

    def __str__(self):
        return f"{self.weight}:{self.title}"

    def get_absolute_url(self):
        return reverse(self.absolute_url)

    def pypi_name(self):
        key = f"SEARCH_PYPI_NAME-{self.slug}"
        pypi_name = cache.get(key)
        if pypi_name:
            return pypi_name
        try:
            package = Package.objects.get(slug=self.slug)
        except Package.DoesNotExist:
            return ""
        pypi_name = package.pypi_name
        cache.set(key, pypi_name, 24 * 60 * 60)
        return pypi_name

    def get_resource_uri(self):
        return f"/api/v4/{self.item_type}/3/"

    def _self(self):
        return self
