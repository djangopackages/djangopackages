import pytest
from package.repos.repo_url_normelizer import normalize_repo_url, RepoURLError


class TestNormalizeRepoURL:
    @pytest.mark.parametrize(
        "url,expected",
        [
            # GitHub
            ("https://github.com/django/django", "https://github.com/django/django"),
            ("http://github.com/django/django", "https://github.com/django/django"),
            ("github.com/django/django", "https://github.com/django/django"),
            (
                "https://www.github.com/django/django",
                "https://github.com/django/django",
            ),
            (
                "https://github.com/django/django.git",
                "https://github.com/django/django",
            ),
            ("git@github.com:django/django.git", "https://github.com/django/django"),
            # GitHub with markers
            (
                "https://github.com/django/django/tree/main",
                "https://github.com/django/django",
            ),
            (
                "https://github.com/django/django/blob/master/README.rst",
                "https://github.com/django/django",
            ),
            (
                "https://github.com/django/django/issues",
                "https://github.com/django/django",
            ),
            (
                "https://github.com/django/django/pulls",
                "https://github.com/django/django",
            ),
            # Bitbucket
            (
                "https://bitbucket.org/atlassian/python-bitbucket",
                "https://bitbucket.org/atlassian/python-bitbucket",
            ),
            (
                "git@bitbucket.org:atlassian/python-bitbucket.git",
                "https://bitbucket.org/atlassian/python-bitbucket",
            ),
            # Codeberg
            (
                "https://codeberg.org/forgejo/forgejo",
                "https://codeberg.org/forgejo/forgejo",
            ),
            # Case insensitivity
            ("https://GitHub.com/Django/Django", "https://github.com/django/django"),
        ],
    )
    def test_simple_providers(self, url, expected):
        assert normalize_repo_url(url) == expected

    @pytest.mark.parametrize(
        "url,expected",
        [
            # GitLab (nested groups support)
            (
                "https://gitlab.com/gitlab-org/gitlab",
                "https://gitlab.com/gitlab-org/gitlab",
            ),
            (
                "https://gitlab.com/group/subgroup/project",
                "https://gitlab.com/group/subgroup/project",
            ),
            (
                "git@gitlab.com:group/subgroup/project.git",
                "https://gitlab.com/group/subgroup/project",
            ),
            (
                "https://gitlab.com/group/subgroup/project/-/tree/main",
                "https://gitlab.com/group/subgroup/project",
            ),
            (
                "https://gitlab.com/group/subgroup/project/-/merge_requests",
                "https://gitlab.com/group/subgroup/project",
            ),
        ],
    )
    def test_gitlab_provider(self, url, expected):
        assert normalize_repo_url(url) == expected

    @pytest.mark.parametrize(
        "url,expected",
        [
            (
                "https://git.example.com/owner/repo",
                "https://git.example.com/owner/repo",
            ),
            (
                "https://git.example.com/owner/repo.git",
                "https://git.example.com/owner/repo",
            ),
            # Unknown provider assumes simple owner/repo structure and takes first 2 segments
            (
                "https://git.example.com/owner/repo/extra/path",
                "https://git.example.com/owner/repo",
            ),
        ],
    )
    def test_unknown_provider(self, url, expected):
        assert normalize_repo_url(url) == expected

    def test_unknown_provider_not_allowed(self):
        url = "https://git.example.com/owner/repo"
        with pytest.raises(RepoURLError, match="Unknown provider"):
            normalize_repo_url(url, allow_unknown=False)

    def test_allowed_hosts(self):
        allowed = {"github.com", "gitlab.com"}

        # Allowed
        assert (
            normalize_repo_url(
                "https://github.com/django/django", allowed_hosts=allowed
            )
            == "https://github.com/django/django"
        )

        # Not allowed
        with pytest.raises(
            RepoURLError, match="Host 'bitbucket.org' not in allowed list"
        ):
            normalize_repo_url(
                "https://bitbucket.org/owner/repo", allowed_hosts=allowed
            )

    @pytest.mark.parametrize(
        "url",
        [
            "",
            "   ",
            "not-a-url",
            "https://github.com",
            "https://github.com/",
            "https://github.com/owner",
            "https://github.com/owner/",
        ],
    )
    def test_invalid_urls(self, url):
        with pytest.raises(RepoURLError):
            normalize_repo_url(url)
