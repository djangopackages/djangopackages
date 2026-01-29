import pytest
from unittest.mock import patch, Mock

from package.models import Package
from package.repos.codeberg import CodebergHandler
from package.repos.forgejo import ForgejoClient, ForgejoMetadata


class MockClient(ForgejoClient):
    """VCR is currently not setup so instead of creating requests to live
    services use a mock to test basic functionality such as extracting
    participants and archiving packages.
    """

    def __init__(self):
        super().__init__("https://codeberg.org")

    meta = ForgejoMetadata(
        archived=False,
        archived_at=None,
        description="test description",
        forks_count=20,
        stars_count=100,
        watchers_count=5,
    )

    def fetch_repository(self, repository: str) -> ForgejoMetadata | None:
        return self.meta


def test_repos_codeberg(package_codeberg):
    handler = CodebergHandler()
    handler.client = MockClient()

    assert package_codeberg.commit_count == 0

    # Mock requests.get for _fetch_commit_stats
    with patch("package.repos.forgejo.requests.get") as mock_get:
        # Mock response for single commit (latest)
        mock_resp_latest = Mock()
        mock_resp_latest.json.return_value = [
            {
                "commit": {
                    "committer": {"date": "2024-12-20T14:20:00Z"},
                    "message": "latest commit",
                }
            }
        ]
        mock_resp_latest.headers = {"X-Total-Count": "3"}

        # Mock response for 52-week histogram (all commits)
        mock_resp_all = Mock()
        mock_resp_all.json.return_value = [
            {"commit": {"committer": {"date": "2024-12-20T14:20:00Z"}}},
            {"commit": {"committer": {"date": "2024-12-20T14:20:00Z"}}},
            {"commit": {"committer": {"date": "2024-12-20T14:20:00Z"}}},
        ]

        # Mock empty response to stop pagination
        mock_resp_empty = Mock()
        mock_resp_empty.json.return_value = []

        mock_get.side_effect = [mock_resp_latest, mock_resp_all, mock_resp_empty]

        handler.fetch_metadata(package_codeberg)

    package = Package.objects.get(id=package_codeberg.id)
    assert package.repo_description == handler.client.meta.description
    assert package.repo_watchers == handler.client.meta.watchers_count

    # Assert new stats fields
    assert package.commit_count == 3
    assert isinstance(package.commits_over_52w, list)
    # Check that commits_over_52w is populated (list of 52 ints)
    assert len(package.commits_over_52w) == 52


def test_repos_codeberg_archived(package_codeberg):
    handler = CodebergHandler()
    handler.client = MockClient()
    handler.client.meta.archived = True
    handler.client.meta.archived_at = "2024-12-20T14:20:00Z"

    assert package_codeberg.date_repo_archived is None

    # We need to mock requests here too because fetch_metadata calls _fetch_commit_stats
    with patch("package.repos.forgejo.requests.get") as mock_get:
        # Latest commit response
        mock_resp_latest = Mock()
        mock_resp_latest.json.return_value = [
            {"commit": {"committer": {"date": "2024-12-20T14:20:00Z"}}}
        ]
        mock_resp_latest.headers = {"X-Total-Count": "0"}

        # Loop response (page 1) - can be empty or have data
        mock_resp_loop = Mock()
        mock_resp_loop.json.return_value = []

        mock_get.side_effect = [mock_resp_latest, mock_resp_loop]

        handler.fetch_metadata(package_codeberg)

    package = Package.objects.get(id=package_codeberg.id)
    assert package.date_repo_archived.hour == 14


@pytest.mark.skip(reason="live request for debugging purpose only")
def test_repos_codeberg_live(package_codeberg):
    handler = CodebergHandler()

    assert package_codeberg.commit_count == 0

    handler.fetch_metadata(package_codeberg)

    package = Package.objects.get(id=package_codeberg.id)
    assert package.repo_description == "test description"
    assert package.commit_count > 0
