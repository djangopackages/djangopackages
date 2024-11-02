import pytest

from package.repos.gitlab import GitLabHandler


@pytest.fixture()
def gitlab_handler():
    return GitLabHandler()


# @pytest.mark.vcr()
# def test_gitlab_fetch_commits(gitlab_handler, package_gitlab):
#     assert Commit.objects.count() == 0
#     gitlab_handler.fetch_commits(package_gitlab)
#     assert Commit.objects.count() > 0


# @pytest.mark.vcr()
# def test_gitlab_fetch_metadata(gitlab_handler, package_gitlab):
#     assert package_gitlab.repo_watchers == 0
#     assert package_gitlab.repo_forks == 0
#     package = gitlab_handler.fetch_metadata(package_gitlab)
#     assert package.repo_description.startswith(
#         "A set of fields that wrap standard Django fields with encryption provided by the python cryptography library."
#     )
#     assert package.repo_watchers == 33
#     assert package.repo_forks == 25
#     assert package.participants == ""


# @pytest.mark.vcr()
# def test_gitlab_fetch_metadata_archived_repo(gitlab_handler, package_gitlab_archived):
#     # test what happens when we reference an archived repository
#     assert package_gitlab_archived.date_repo_archived is None
#     package = gitlab_handler.fetch_metadata(package_gitlab_archived)

#     assert package_gitlab_archived.date_repo_archived is not None
#     assert package.repo_description.startswith("Metadata package for models.")
#     assert package.date_repo_archived is not None


# @pytest.mark.vcr()
# def test_gitlab_fetch_metadata_unsupported_repo(gitlab_handler, package_gitlab_invalid):
#     # test what happens when setting up an unsupported repository
#     assert (
#         package_gitlab_invalid.repo_url
#         == "https://gitlab.com/jeff.triplett/does-not-exist"
#     )

#     with pytest.raises(GitlabGetError):
#         gitlab_handler.fetch_metadata(package_gitlab_invalid)
