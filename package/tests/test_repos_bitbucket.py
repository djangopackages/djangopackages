import pytest

from package.repos.bitbucket import BitbucketHandler


@pytest.fixture()
def bitbucket_handler():
    return BitbucketHandler()


def test_bitbucket_handler_matches_dotted_usernames():
    from package.repos import get_repo_for_repo_url
    from package.repos.bitbucket import BitbucketHandler

    handler = get_repo_for_repo_url("https://bitbucket.org/dias.kev/django-quotidian")
    assert isinstance(handler, BitbucketHandler)
