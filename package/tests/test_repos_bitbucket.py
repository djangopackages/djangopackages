import pytest

from package.repos.bitbucket import BitbucketHandler


@pytest.fixture()
def bitbucket_handler():
    return BitbucketHandler()
