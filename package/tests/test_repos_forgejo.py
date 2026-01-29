from unittest.mock import patch, Mock
from package.models import Package
from package.repos.forgejo import ForgejoHandler, ForgejoMetadata


class MockForgejoClient:
    meta = ForgejoMetadata(
        archived=False,
        archived_at=None,
        description="forgejo description",
        forks_count=7,
        stars_count=42,
        watchers_count=3,
    )

    def fetch_repository(self, repository: str) -> ForgejoMetadata | None:
        return self.meta


def test_forgejo_handler_updates_package(package_forgejo):
    handler = ForgejoHandler()
    handler.client = MockForgejoClient()

    assert package_forgejo.commit_count == 0

    with patch("package.repos.forgejo.requests.get") as mock_get:
        # Mock responses
        mock_resp_latest = Mock()
        mock_resp_latest.json.return_value = [
            {"commit": {"committer": {"date": "2025-01-01T00:00:00Z"}}}
        ]
        mock_resp_latest.headers = {"X-Total-Count": "2"}

        mock_resp_all = Mock()
        mock_resp_all.json.return_value = [
            {"commit": {"committer": {"date": "2025-01-01T00:00:00Z"}}},
            {"commit": {"committer": {"date": "2025-01-02T00:00:00Z"}}},
        ]

        # Mock empty response to stop pagination
        mock_resp_empty = Mock()
        mock_resp_empty.json.return_value = []

        mock_get.side_effect = [mock_resp_latest, mock_resp_all, mock_resp_empty]

        handler.fetch_metadata(package_forgejo)

    package = Package.objects.get(id=package_forgejo.id)
    assert package.repo_description == handler.client.meta.description
    assert package.repo_watchers == handler.client.meta.watchers_count
    assert package.repo_forks == handler.client.meta.forks_count
    assert package.commit_count == 2
    assert len(package.commits_over_52w) == 52


def test_forgejo_extract_repo_name_strips_git_suffix():
    handler = ForgejoHandler()
    repo_url = "https://git.example.com/example/forgejo-repo.git"
    assert handler.extract_repo_name(repo_url) == "example/forgejo-repo"
