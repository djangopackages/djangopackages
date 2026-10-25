from django.urls import reverse
from django.utils import timezone
from model_bakery import baker

from package.models import Package
from package.scores import update_package_score


def test_rules_page_total_matches_stored_score(db, client, category):
    package = baker.make(
        Package,
        category=category,
        slug="scored",
        repo_url="https://github.com/t/scored",
        repo_watchers=100,
        repo_description="A package",
        last_commit_date=timezone.now(),
    )
    update_package_score(package, save=True)

    response = client.get(reverse("package_rules", kwargs={"slug": "scored"}))

    assert response.status_code == 200
    assert response.context["package_score"]["total_score"] == package.score
    assert len(response.context["package_score"]["breakdown"]) == 9


def test_dormant_package_page_says_so(db, client, category):
    package = baker.make(
        Package,
        category=category,
        slug="dormant",
        repo_url="https://github.com/t/dormant",
        repo_watchers=3000,
        last_commit_date=timezone.now() - timezone.timedelta(days=365 * 6),
    )
    update_package_score(package, save=True)
    assert package.score == 0

    response = client.get(reverse("package", kwargs={"slug": "dormant"}))

    assert response.status_code == 200
    assert "No release or commit since" in response.content.decode()
