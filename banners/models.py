from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from core.models import BaseModel


class BannerQuerySet(models.QuerySet):
    def active(self):
        """Return banners that are currently live.

        A banner is active when:
        - start_date <= now
        - end_date is null OR end_date > now
        """
        now = timezone.now()
        return (
            self.filter(start_date__lte=now)
            .exclude(end_date__isnull=False, end_date__lte=now)
            .order_by("-created")
        )


class BannerType(models.TextChoices):
    SPONSORED = "sponsored", _("Sponsored")
    NOTICE = "notice", _("Notice")
    SUCCESS = "success", _("Success")
    WARNING = "warning", _("Warning")
    CRITICAL = "critical", _("Critical")


class BannerAlignment(models.TextChoices):
    LEFT = "left", _("Left")
    CENTER = "center", _("Center")
    RIGHT = "right", _("Right")


# Default Phosphor icons per banner type
BANNER_TYPE_ICONS = {
    BannerType.SPONSORED: "ph-star",
    BannerType.NOTICE: "ph-megaphone",
    BannerType.SUCCESS: "ph-check-circle",
    BannerType.WARNING: "ph-warning",
    BannerType.CRITICAL: "ph-warning-octagon",
}


class Banner(BaseModel):
    """A time-based site-wide banner displayed below the navbar."""

    title = models.CharField(
        _("title"),
        max_length=200,
        help_text=_("Admin-facing label for this banner."),
    )
    content = models.TextField(
        _("content"),
        help_text=_("Banner body text. HTML is supported."),
    )
    banner_type = models.CharField(
        _("banner type"),
        max_length=20,
        choices=BannerType,
        default=BannerType.NOTICE,
        help_text=_("Determines the visual style of the banner."),
    )
    start_date = models.DateTimeField(
        _("start date"),
        help_text=_("When the banner becomes visible."),
    )
    end_date = models.DateTimeField(
        _("end date"),
        blank=True,
        null=True,
        help_text=_("When the banner expires. Leave blank for indefinite display."),
    )
    is_dismissible = models.BooleanField(
        _("dismissible"),
        default=True,
        help_text=_("Whether users can dismiss this banner."),
    )
    icon = models.CharField(
        _("icon override"),
        max_length=100,
        blank=True,
        help_text=_(
            "Phosphor icon class override (e.g. 'ph-megaphone'). "
            "Leave blank to use the default icon for the banner type."
        ),
    )
    alignment = models.CharField(
        _("content alignment"),
        max_length=10,
        choices=BannerAlignment,
        default=BannerAlignment.LEFT,
        help_text=_("Horizontal alignment of the banner content."),
    )

    objects = BannerQuerySet.as_manager()

    class Meta:
        ordering = ["-created"]
        verbose_name = _("banner")
        verbose_name_plural = _("banners")

    def __str__(self):
        return self.title

    @property
    def display_icon(self):
        """Return the icon class to use — custom override or default for type."""
        if self.icon:
            return self.icon
        return BANNER_TYPE_ICONS.get(self.banner_type, "ph-info")
