import pytest

from package.repos.bitbucket import BitbucketHandler


@pytest.fixture()
def bitbucket_handler():
    return BitbucketHandler()


# @pytest.mark.vcr()
# def test_bitbucket_fetch_commits(bitbucket_handler, package_bitbucket):
#     assert Commit.objects.count() == 0
#     bitbucket_handler.fetch_commits(package_bitbucket)
#     assert Commit.objects.count() == 27


# @pytest.mark.vcr()
# def test_bitbucket_fetch_metadata(bitbucket_handler, package_bitbucket):
#     assert package_bitbucket.repo_watchers == 0
#     assert package_bitbucket.repo_forks == 0
#     package = bitbucket_handler.fetch_metadata(package_bitbucket)
#     assert package.repo_description.startswith(
#         "Microsoft SQL server backend for Django running on windows"
#     )
#     assert package.repo_watchers == 10
#     assert package.repo_forks == 10
#     assert package.participants == "Manfre"
