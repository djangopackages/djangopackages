import pytest

from package.repos.github import GitHubHandler


@pytest.fixture()
def github_handler():
    return GitHubHandler()


# @pytest.mark.vcr()
# def test_github_fetch_commits(github_handler, package):
#     assert Commit.objects.count() == 0
#     github_handler.fetch_commits(package)
#     assert Commit.objects.count() > 0


# @pytest.mark.vcr()
# def test_github_fetch_metadata(github_handler, package):
#     # Currently a live tests that access github
#     package = github_handler.fetch_metadata(package)
#     assert package.repo_description == "Django Enhancement Proposals"
#     assert package.repo_watchers > 100


# @pytest.mark.vcr()
# def test_github_fetch_metadata_archived_repo(github_handler, package_archived):
#     # test what happens when we reference an archived repository
#     assert package_archived.date_repo_archived is None
#     package = github_handler.fetch_metadata(package_archived)

#     assert package_archived.date_repo_archived is not None
#     assert package.repo_description == "Django + Pagination made easy."
#     assert package.date_repo_archived is not None


# @pytest.mark.vcr()
# def test_github_fetch_metadata_unsupported_repo(github_handler, package_invalid):
#     # test what happens when setting up an unsupported repository
#     assert (
#         package_invalid.repo_url == "https://github.com/djangopackages/does-not-exist"
#     )

#     with pytest.raises(NotFoundError):
#         github_handler.fetch_metadata(package_invalid)
