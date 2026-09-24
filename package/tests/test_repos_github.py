from unittest.mock import Mock, patch

import pytest

from package.models import Package
from package.repos.github import GitHubHandler


@pytest.fixture()
def github_handler():
    return GitHubHandler()


def _mock_github_repo(*, homepage):
    repo = Mock()
    repo.archived = False
    repo.description = "A probe for Django apps"
    repo.forks_count = 1
    repo.watchers_count = 2
    repo.homepage = homepage
    repo.contributors.return_value = []
    return repo


def test_github_sets_documentation_url_from_homepage(package, github_handler):
    package.documentation_url = ""
    package.save()
    repo = _mock_github_repo(homepage="https://djangoprobe.org")

    with (
        patch.object(github_handler, "_get_repo", return_value=repo),
        patch.object(github_handler, "_fetch_commit_stats"),
        patch.object(github_handler, "manage_ratelimit"),
    ):
        github_handler.fetch_metadata(package)

    package = Package.objects.get(id=package.id)
    assert package.documentation_url == "https://djangoprobe.org"


def test_github_skips_homepage_that_points_at_repo(package, github_handler):
    package.documentation_url = ""
    package.save()
    repo = _mock_github_repo(homepage=package.repo_url)

    with (
        patch.object(github_handler, "_get_repo", return_value=repo),
        patch.object(github_handler, "_fetch_commit_stats"),
        patch.object(github_handler, "manage_ratelimit"),
    ):
        github_handler.fetch_metadata(package)

    package = Package.objects.get(id=package.id)
    assert package.documentation_url in {"", None}


def test_github_does_not_overwrite_existing_documentation_url(package, github_handler):
    package.documentation_url = "https://manual.example.com"
    package.save()
    repo = _mock_github_repo(homepage="https://djangoprobe.org")

    with (
        patch.object(github_handler, "_get_repo", return_value=repo),
        patch.object(github_handler, "_fetch_commit_stats"),
        patch.object(github_handler, "manage_ratelimit"),
    ):
        github_handler.fetch_metadata(package)

    package = Package.objects.get(id=package.id)
    assert package.documentation_url == "https://manual.example.com"
