"""The repository host breakdown on /open/.

repo_host is empty for nearly every package, so the URL is what places them.
These cover the placing, the percentages, and the "Other" bucket that catches
a forge the URL cannot name.
"""

import pytest
from django.urls import reverse
from model_bakery import baker

from homepage.views import repo_host_breakdown
from package.models import Category, Package, RepoHost


@pytest.fixture()
def category(db):
    return baker.make(Category, slug="apps", title="App", title_plural="Apps")


def make_package(category, slug, repo_url, repo_host=RepoHost.AUTO_DETECT):
    return baker.make(
        Package,
        slug=slug,
        title=slug,
        category=category,
        repo_url=repo_url,
        repo_host=repo_host,
    )


@pytest.fixture()
def hosted_packages(category):
    make_package(category, "a", "https://github.com/example/a")
    make_package(category, "b", "https://github.com/example/b")
    make_package(category, "c", "https://gitlab.com/example/c")
    make_package(category, "d", "https://codeberg.org/example/d")


@pytest.mark.django_db
def test_hosts_are_placed_from_the_url(hosted_packages):
    rows = {row["slug"]: row for row in repo_host_breakdown()["rows"]}

    assert rows["github"]["count"] == 2
    assert rows["gitlab"]["count"] == 1
    assert rows["codeberg"]["count"] == 1
    assert "bitbucket" not in rows


@pytest.mark.django_db
def test_percentages_are_of_the_active_total(hosted_packages):
    breakdown = repo_host_breakdown()
    rows = {row["slug"]: row for row in breakdown["rows"]}

    assert breakdown["total"] == 4
    assert rows["github"]["percent"] == 50.0
    assert rows["gitlab"]["percent"] == 25.0


@pytest.mark.django_db
def test_rows_are_largest_first(hosted_packages):
    counts = [row["count"] for row in repo_host_breakdown()["rows"]]

    assert counts == sorted(counts, reverse=True)


@pytest.mark.django_db
def test_an_unknown_forge_lands_in_other(category):
    make_package(category, "a", "https://github.com/example/a")
    make_package(category, "self", "https://git.example.org/team/self")

    rows = {row["slug"]: row for row in repo_host_breakdown()["rows"]}

    assert rows["other"]["count"] == 1
    assert rows["other"]["percent"] == 50.0


@pytest.mark.django_db
def test_an_explicit_repo_host_wins_over_the_url(category):
    """What the field exists for: a self-hosted forge the URL cannot name."""
    make_package(
        category,
        "self",
        "https://git.example.org/team/self",
        repo_host=RepoHost.FORGEJO,
    )

    rows = {row["slug"]: row for row in repo_host_breakdown()["rows"]}

    assert rows["forgejo"]["count"] == 1
    assert "other" not in rows


@pytest.mark.django_db
def test_a_host_with_no_packages_is_left_out(hosted_packages):
    """A zero slice is a legend entry that says nothing."""
    slugs = [row["slug"] for row in repo_host_breakdown()["rows"]]

    assert "forgejo" not in slugs
    assert "bitbucket" not in slugs


@pytest.mark.django_db
def test_no_packages_at_all_does_not_divide_by_zero(db):
    breakdown = repo_host_breakdown()

    assert breakdown["total"] == 0
    assert breakdown["rows"] == []


@pytest.mark.django_db
def test_the_open_page_renders_the_chart(client, hosted_packages):
    response = client.get(reverse("open"))

    assert response.status_code == 200
    assert b'id="chart_repo_hosts"' in response.content
    assert b'id="repo-hosts-data"' in response.content
    assert response.context["repo_hosts"]["total"] == 4
