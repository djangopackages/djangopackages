import datetime

import pytest
from django.test import Client
from django.urls import reverse
from django.utils import timezone
from model_bakery import baker

from banners.models import Banner


@pytest.mark.django_db
class TestDismissBannerView:
    def test_dismiss_sets_session_flag(self):
        banner = baker.make(
            Banner,
            title="Active Banner",
            start_date=timezone.now() - datetime.timedelta(hours=1),
            end_date=None,
        )
        client = Client()
        url = reverse("banners:dismiss", kwargs={"banner_id": banner.pk})
        response = client.post(url)

        assert response.status_code == 200
        assert response.content == b""
        assert client.session.get(f"dismissed_banner_{banner.pk}") is True
