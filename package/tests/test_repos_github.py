import pytest

from package.repos.github import GitHubHandler


@pytest.fixture()
def github_handler():
    return GitHubHandler()
