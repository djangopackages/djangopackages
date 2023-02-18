from django.db import models
from django.template.defaultfilters import slugify
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from core.models import BaseModel


class Product(BaseModel):
    title = models.CharField(_("Title"), max_length=50)
    slug = models.SlugField(_("slug"))
    active = models.BooleanField(
        _("Active"),
        default=True,
    )

    def __str__(self):
        return f"{self.title}"

    def save(self, **kwargs):
        if self.slug is None:
            self.slug = slugify(self.title)
        super().save(**kwargs)


class Release(BaseModel):
    """
    # see: https://endoflife.date/docs/api

    makemodel Release
    - cycle: number or string - Release Cycle
    - release: string <date> - Release Date for the first release in this cycle
    - eol: string or boolean - End of Life Date for this release cycle
    - latest: string - Latest release in this cycle
    - link: string - Link to changelog for the latest release, if available
    - lts: boolean - Whether this release cycle has long-term-support (LTS)
    - support: string or boolean <date> - Whether this release cycle has active support
    - cycleShortHand: string - Optional shorthand name for this release cycle
    - discontinued: string or boolean <date> - Whether this cycle is now discontinued.
    """

    product = models.ForeignKey("Product", on_delete=models.CASCADE)
    cycle = models.CharField(_("Release Cycle"), max_length=50)  # : number or string -
    cycle_short_hand = models.CharField(
        _("Shorthand name"), max_length=100, blank=True, null=True
    )  # : string - Optional shorthand name for this release cycle
    codename = models.CharField(
        _("Code name"), max_length=100, blank=True, null=True
    )  # : string - Optional shorthand name for this release cycle
    release = models.DateField(
        _("Release Date"), max_length=50, blank=True, null=True
    )  # : string <date> - Release Date for the first release in this cycle
    eol = models.DateField(
        _("End of Life Date"), max_length=50, blank=True, null=True
    )  # : string or boolean - End of Life Date for this release cycle
    latest = models.CharField(
        _("Latest release"), max_length=50, blank=True, null=True
    )  # : string - Latest release in this cycle
    link = models.CharField(
        _("Link to changelog"), max_length=200, blank=True, null=True
    )  # : string - Link to changelog for the latest release, if available
    lts = models.BooleanField(
        _("Long-term-support"), max_length=50, default=False
    )  # : boolean - Whether this release cycle has long-term-support (LTS)
    support = models.CharField(
        _("Has active support"), max_length=50, blank=True, null=True
    )  # : string or boolean <date> - Whether this release cycle has active support
    discontinued = models.CharField(
        _("Discontinued"), max_length=50, blank=True, null=True
    )  # : string or boolean <date> - Whether this cycle is now discontinued.

    def __str__(self):
        return f"{self.product.title} {self.cycle}"

    @property
    def is_eol(self):
        if self.eol:
            return self.eol < timezone.now().date()
        return None
