import datetime

import pytest
from django.test import RequestFactory
from django.utils import timezone
from model_bakery import baker

from banners.context_processors import active_banner
from banners.models import Banner


@pytest.mark.django_db
class TestBannerContextProcessor:
    def test_active_banners_in_context(self):
        banner = baker.make(
            Banner,
            title="Active Banner",
            start_date=timezone.now() - datetime.timedelta(hours=1),
            end_date=None,
        )
        request = RequestFactory().get("/")
        context = active_banner(request)
        assert banner in context["active_banners"]

    def test_multiple_active_banners_in_context(self):
        banner1 = baker.make(
            Banner,
            title="Banner 1",
            start_date=timezone.now() - datetime.timedelta(hours=2),
            end_date=None,
        )
        banner2 = baker.make(
            Banner,
            title="Banner 2",
            start_date=timezone.now() - datetime.timedelta(hours=1),
            end_date=None,
        )
        request = RequestFactory().get("/")
        context = active_banner(request)
        assert banner1 in context["active_banners"]
        assert banner2 in context["active_banners"]

    def test_no_active_banners_in_context(self):
        request = RequestFactory().get("/")
        context = active_banner(request)
        assert context["active_banners"] == []

    def test_expired_banner_not_in_context(self):
        now = timezone.now()
        baker.make(
            Banner,
            title="Expired Banner",
            start_date=now - datetime.timedelta(days=2),
            end_date=now - datetime.timedelta(days=1),
        )
        request = RequestFactory().get("/")
        context = active_banner(request)
        assert context["active_banners"] == []

    def test_dismissed_banner_excluded_from_context(self):
        """A banner dismissed in the session should not appear in context."""
        banner = baker.make(
            Banner,
            title="Dismissed Banner",
            start_date=timezone.now() - datetime.timedelta(hours=1),
            end_date=None,
        )
        request = RequestFactory().get("/")
        request.session = {f"dismissed_banner_{banner.pk}": True}
        context = active_banner(request)
        assert banner not in context["active_banners"]

    def test_only_dismissed_banner_excluded_when_multiple_active(self):
        """Only the dismissed banner is filtered out; others still show."""
        kept = baker.make(
            Banner,
            title="Kept Banner",
            start_date=timezone.now() - datetime.timedelta(hours=2),
            end_date=None,
        )
        dismissed = baker.make(
            Banner,
            title="Dismissed Banner",
            start_date=timezone.now() - datetime.timedelta(hours=1),
            end_date=None,
        )
        request = RequestFactory().get("/")
        request.session = {f"dismissed_banner_{dismissed.pk}": True}
        context = active_banner(request)
        assert kept in context["active_banners"]
        assert dismissed not in context["active_banners"]
