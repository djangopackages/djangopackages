import pytest

from package.models import Commit
from package.repos.gitlab import GitlabHandler


@pytest.fixture()
def gitlab_handler():
    return GitlabHandler()


def test_fetch_commits(gitlab_handler, package_gitlab):
    assert Commit.objects.count() == 0
    gitlab_handler.fetch_commits(package_gitlab)
    assert Commit.objects.count() > 0


def test_fetch_metadata(gitlab_handler, package_gitlab):
    assert package_gitlab.repo_watchers == 0
    assert package_gitlab.repo_forks == 0
    package = gitlab_handler.fetch_metadata(package_gitlab)
    assert package.repo_description.startswith(
        "A minimalistic API-driven case management system"
    )
    assert package.repo_watchers == 1
    assert package.repo_forks == 0
    assert package.participants == ""
