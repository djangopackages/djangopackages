import datetime

import pytest
from django.utils import timezone
from model_bakery import baker

from banners.models import Banner, BannerType

# Time is frozen by the autouse `set_time` fixture in conftest.py via time_machine.
# Use timezone.now() directly so tests stay correct if the freeze point ever changes.


@pytest.mark.django_db
class TestBannerModel:
    def test_display_icon_default(self):
        banner = baker.make(Banner, banner_type=BannerType.NOTICE, icon="")
        assert banner.display_icon == "ph-megaphone"

    def test_display_icon_custom_override(self):
        banner = baker.make(Banner, banner_type=BannerType.NOTICE, icon="ph-gear")
        assert banner.display_icon == "ph-gear"

    def test_get_active_banner_returns_latest(self):
        """When multiple banners are active, the most recently created wins."""
        now = timezone.now()
        baker.make(
            Banner,
            title="Older",
            start_date=now - datetime.timedelta(hours=2),
            end_date=None,
        )
        newer = baker.make(
            Banner,
            title="Newer",
            start_date=now - datetime.timedelta(hours=1),
            end_date=None,
        )
        result = Banner.objects.active().first()
        assert result == newer

    def test_get_active_banner_excludes_expired(self):
        """Banners whose end_date has passed should not be returned."""
        now = timezone.now()
        baker.make(
            Banner,
            title="Expired",
            start_date=now - datetime.timedelta(days=2),
            end_date=now - datetime.timedelta(days=1),
        )
        assert Banner.objects.active().first() is None

    def test_get_active_banner_excludes_future(self):
        """Banners whose start_date is in the future should not be returned."""
        baker.make(
            Banner,
            title="Future",
            start_date=timezone.now() + datetime.timedelta(days=1),
            end_date=None,
        )
        assert Banner.objects.active().first() is None

    def test_get_active_banner_with_no_end_date(self):
        """A banner with no end_date is perpetually active once started."""
        banner = baker.make(
            Banner,
            title="Indefinite",
            start_date=timezone.now() - datetime.timedelta(hours=1),
            end_date=None,
        )
        assert Banner.objects.active().first() == banner

    def test_get_active_banner_exact_start_date(self):
        """A banner whose start_date equals now should be included."""
        banner = baker.make(
            Banner,
            title="Exact start",
            start_date=timezone.now(),
            end_date=None,
        )
        assert Banner.objects.active().first() == banner

    def test_get_active_banner_exact_end_date(self):
        """A banner whose end_date equals now should be excluded (end_date__lte=now)."""
        now = timezone.now()
        baker.make(
            Banner,
            title="Exact end",
            start_date=now - datetime.timedelta(hours=1),
            end_date=now,
        )
        assert Banner.objects.active().first() is None
