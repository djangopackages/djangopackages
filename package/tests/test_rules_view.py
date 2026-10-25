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
    assert len(response.context["package_score"]["breakdown"]) == 7


def test_faded_package_page_says_so(db, client, category):
    package = baker.make(
        Package,
        category=category,
        slug="faded",
        repo_url="https://github.com/t/faded",
        repo_watchers=3000,
        repo_description="x",
        last_commit_date=timezone.now() - timezone.timedelta(days=365 * 4),
    )
    update_package_score(package, save=True)
    # not deprecated 20, description 20, watchers 20 = 60 of 120 = 50, a quarter of it.
    assert package.score == 12

    response = client.get(reverse("package", kwargs={"slug": "faded"}))

    assert response.status_code == 200
    html = response.content.decode()
    assert "Not on PyPI, and last commit" in html
    assert "keeps 25% of the points" in html
