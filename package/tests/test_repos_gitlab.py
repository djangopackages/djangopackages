import pytest

from package.repos.gitlab import GitLabHandler


@pytest.fixture()
def gitlab_handler():
    return GitLabHandler()
