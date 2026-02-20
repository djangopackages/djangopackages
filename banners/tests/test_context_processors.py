import datetime

import pytest
from django.test import RequestFactory
from django.utils import timezone
from model_bakery import baker

from banners.context_processors import active_banner
from banners.models import Banner


@pytest.mark.django_db
class TestBannerContextProcessor:
    def test_active_banner_in_context(self):
        banner = baker.make(
            Banner,
            title="Active Banner",
            start_date=timezone.now() - datetime.timedelta(hours=1),
            end_date=None,
        )
        request = RequestFactory().get("/")
        context = active_banner(request)
        assert context["active_banner"] == banner

    def test_no_active_banner_in_context(self):
        request = RequestFactory().get("/")
        context = active_banner(request)
        assert context["active_banner"] is None

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
        assert context["active_banner"] is None

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
        assert context["active_banner"] is None
