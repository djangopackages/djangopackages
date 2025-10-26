from package.models import Package
from package.repos.forgejo import ForgejoCommit, ForgejoHandler, ForgejoMetadata


class MockForgejoClient:
    meta = ForgejoMetadata(
        archived=False,
        archived_at=None,
        description="forgejo description",
        forks_count=7,
        stars_count=42,
        watchers_count=3,
    )

    commits = [
        ForgejoCommit("abc", "2025-01-01T00:00", "alice"),
        ForgejoCommit("def", "2025-01-02T00:00", "bob"),
    ]

    def fetch_repository(self, repository: str) -> ForgejoMetadata | None:
        return self.meta

    def fetch_commits(self, repository: str, page_size=50):
        return self.commits


def test_forgejo_handler_updates_package(package_forgejo):
    handler = ForgejoHandler()
    handler.client = MockForgejoClient()

    assert package_forgejo.commit_set.count() == 0

    handler.fetch_metadata(package_forgejo)
    handler.fetch_commits(package_forgejo)

    package = Package.objects.get(id=package_forgejo.id)
    assert package.repo_description == handler.client.meta.description
    assert package.repo_watchers == handler.client.meta.stars_count
    assert package.repo_forks == handler.client.meta.forks_count
    assert package.commit_set.count() == 2
    assert "alice" in package.participants
    assert "bob" in package.participants


def test_forgejo_extract_repo_name_strips_git_suffix():
    handler = ForgejoHandler()
    repo_url = "https://git.example.com/example/forgejo-repo.git"
    assert handler.extract_repo_name(repo_url) == "example/forgejo-repo"
