from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone
from model_bakery import baker

from package.models import Category, Package, Version


@pytest.fixture
def scored_package(db):
    category = Category.objects.create(title="Apps", slug="apps")
    package = baker.make(
        Package,
        title="Scored",
        slug="scored",
        category=category,
        repo_url="https://github.com/t/scored",
        repo_watchers=1_234,
        pypi_downloads=56_789,
        last_commit_date=timezone.now() - timedelta(days=10),
    )
    version = Version.objects.create(
        package=package, number="1.0", upload_time=timezone.now() - timedelta(days=20)
    )
    package.latest_version = version
    package.save()
    return package


def test_score_page_shows_the_working(client, scored_package):
    response = client.get(reverse("package_rules", kwargs={"slug": "scored"}))

    assert response.status_code == 200
    content = response.content.decode()
    assert f"Package Score: {response.context['breakdown'].score}" in content
    assert "1,234" in content
    assert "56,789" in content
    assert "Latest release" in content
    assert "Latest commit" in content
    assert "Popularity" in content and "maintenance" in content


def test_score_page_explains_a_zero(client, scored_package):
    scored_package.date_repo_archived = timezone.now()
    scored_package.save()

    response = client.get(reverse("package_rules", kwargs={"slug": "scored"}))

    assert response.status_code == 200
    assert "Package Score: 0" in response.content.decode()
    assert "archived" in response.content.decode()
