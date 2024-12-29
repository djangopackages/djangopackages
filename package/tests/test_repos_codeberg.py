import pytest

from package.models import Package
from package.repos.codeberg import (
    CodebergHandler,
    ForgejoClient,
    ForgejoCommit,
    ForgejoMetadata,
)


class MockClient(ForgejoClient):
    """VCR is currently not setup so instead of creating requests to live
    services use a mock to test basic functionality such as extracting
    participants and archiving packages.
    """

    meta = ForgejoMetadata(
        archived=False,
        archived_at=None,
        description="test description",
        forks_count=20,
        watchers_count=100,
    )

    commits = [
        ForgejoCommit("123", "2024-12-20T14:20", "foo"),
        ForgejoCommit("321", "2024-12-20T14:20", "bar"),
        ForgejoCommit("456", "2024-12-20T14:20", "bar"),
    ]

    def fetch_repository(self, repository: str) -> ForgejoMetadata | None:
        return self.meta

    def fetch_commits(self, repository: str, page_size=50):
        return self.commits


def test_repos_codeberg(package_codeberg):
    handler = CodebergHandler()
    handler.client = MockClient()

    assert package_codeberg.commit_set.count() == 0

    handler.fetch_metadata(package_codeberg)
    handler.fetch_commits(package_codeberg)

    package = Package.objects.get(id=package_codeberg.id)
    assert package.repo_description == handler.client.meta.description
    assert package.commit_set.count() == 3
    assert "foo" in package.participants
    assert "bar" in package.participants
    assert len(package.participants.split(",")) == 2


def test_repos_codeberg_archived(package_codeberg):
    handler = CodebergHandler()
    handler.client = MockClient()
    handler.client.meta.archived = True
    handler.client.meta.archived_at = "2024-12-20T14:20"

    assert package_codeberg.date_repo_archived is None

    handler.fetch_metadata(package_codeberg)

    package = Package.objects.get(id=package_codeberg.id)
    assert package.date_repo_archived.hour == 14


@pytest.mark.skip(reason="live request for debugging purpose only")
def test_repos_codeberg_live(package_codeberg):
    handler = CodebergHandler()

    assert package_codeberg.commit_set.count() == 0

    handler.fetch_metadata(package_codeberg)
    handler.fetch_commits(package_codeberg)

    package = Package.objects.get(id=package_codeberg.id)
    assert package.repo_description == "test description"
    assert package.commit_set.count() == 3
    assert "timo_sams" in package.participants
