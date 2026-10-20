from unittest.mock import Mock, patch

import pytest

from package.models import Package
from package.repos.gitlab import GitLabHandler


@pytest.fixture()
def gitlab_handler():
    return GitLabHandler()


def mock_gitlab_client(project_id=213, default_branch="main"):
    """A python-gitlab stand-in holding just what fetch_metadata reads."""
    repo = Mock()
    repo.id = project_id
    repo.default_branch = default_branch
    repo.archived = False
    repo.description = "gitlab description"
    repo.forks_count = 2
    repo.star_count = 9
    repo.repository_contributors.return_value = [{"name": "levit"}]

    commit = Mock()
    commit.committed_date = "2025-09-19T17:59:44.000Z"
    repo.commits.list.return_value = [commit]

    client = Mock()
    client.projects.get.return_value = repo
    client.http_get.return_value = {"count": 1}
    return client


class TestBaseURL:
    def test_a_custom_instance_is_its_own_base_url(self, gitlab_handler):
        assert (
            gitlab_handler.get_base_url("https://gitlab.levitnet.be/levit/django-fsm")
            == "https://gitlab.levitnet.be"
        )

    def test_gitlab_com_is_unchanged(self, gitlab_handler):
        assert (
            gitlab_handler.get_base_url("https://gitlab.com/group/project")
            == "https://gitlab.com"
        )

    @pytest.mark.parametrize("repo_url", ["", None, "not-a-url"])
    def test_a_url_with_no_host_falls_back_to_gitlab_com(
        self, gitlab_handler, repo_url
    ):
        assert gitlab_handler.get_base_url(repo_url) == "https://gitlab.com"


class TestClients:
    def test_the_token_only_goes_to_gitlab_com(self, gitlab_handler, settings):
        settings.GITLAB_TOKEN = "gitlab-com-token"

        assert gitlab_handler.get_client("https://gitlab.com/g/p").private_token == (
            "gitlab-com-token"
        )
        assert (
            gitlab_handler.get_client("https://gitlab.example.com/g/p").private_token
            is None
        )

    def test_each_instance_gets_its_own_client(self, gitlab_handler):
        first = gitlab_handler.get_client("https://gitlab.example.com/g/p")
        second = gitlab_handler.get_client("https://gitlab.other.com/g/p")

        assert first is not second
        assert first.url == "https://gitlab.example.com"
        assert second.url == "https://gitlab.other.com"

    def test_a_client_is_reused_across_repos_on_one_instance(self, gitlab_handler):
        first = gitlab_handler.get_client("https://gitlab.example.com/g/one")
        second = gitlab_handler.get_client("https://gitlab.example.com/g/two")

        assert first is second


class TestRepoName:
    def test_a_custom_instance_leaves_only_the_path(self, gitlab_handler):
        name = gitlab_handler.extract_repo_name(
            "https://gitlab.levitnet.be/levit/django-fsm-dynamic"
        )
        assert name == "levit/django-fsm-dynamic"

    def test_gitlab_com_still_works(self, gitlab_handler):
        name = gitlab_handler.extract_repo_name("https://gitlab.com/group/project")
        assert name == "group/project"

    def test_nested_groups_are_kept(self, gitlab_handler):
        """GitLab groups nest, and the API wants the whole path."""
        name = gitlab_handler.extract_repo_name(
            "https://gitlab.com/group/subgroup/project"
        )
        assert name == "group/subgroup/project"

    def test_the_git_suffix_is_stripped(self, gitlab_handler):
        name = gitlab_handler.extract_repo_name(
            "https://gitlab.example.com/levit/django-fsm-dynamic.git"
        )
        assert name == "levit/django-fsm-dynamic"


class TestFetchMetadata:
    def test_a_self_hosted_repo_is_fetched_from_its_own_instance(
        self, gitlab_handler, package_gitlab_selfhosted
    ):
        """The regression behind #1459. This used to ask gitlab.com for a
        project path of "https://gitlab.example.com/levit/django-fsm-dynamic"
        and 404, which left every stat at zero.
        """
        client = mock_gitlab_client()
        gitlab_handler.client = client

        gitlab_handler.fetch_metadata(package_gitlab_selfhosted)

        client.projects.get.assert_called_once_with(
            "levit/django-fsm-dynamic", license=True
        )

        package = Package.objects.get(pk=package_gitlab_selfhosted.pk)
        assert package.repo_description == "gitlab description"
        assert package.repo_watchers == 9
        assert package.repo_forks == 2
        assert package.participants == "levit"
        assert package.commit_count == 1
        assert len(package.commits_over_52w) == 52

    def test_commit_stats_use_the_same_instance_as_the_project(
        self, gitlab_handler, package_gitlab_selfhosted
    ):
        """http_get is a raw path, so it has to go through the instance
        client rather than a gitlab.com one.
        """
        with patch.object(gitlab_handler, "get_client") as get_client:
            get_client.return_value = mock_gitlab_client()

            gitlab_handler.fetch_metadata(package_gitlab_selfhosted)

        assert {call.args[0] for call in get_client.call_args_list} == {
            package_gitlab_selfhosted.repo_url
        }
