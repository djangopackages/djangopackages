import pytest
from unittest.mock import Mock, patch, MagicMock
from click.testing import CliRunner
from django.utils import timezone

from package.models import Package, Version, Category
from package.management.commands.package_updater2 import command


@pytest.mark.django_db
class TestPackageUpdater2:
    @pytest.fixture
    def runner(self):
        return CliRunner()

    @pytest.fixture
    def category(self):
        return Category.objects.create(title="Test Category", slug="test-category")

    @pytest.fixture
    def package(self, category):
        return Package.objects.create(
            title="Test Package",
            slug="test-package",
            category=category,
            pypi_url="https://pypi.org/project/test-package/",
            repo_url="https://github.com/test/test-package",
            last_fetched=timezone.now() - timezone.timedelta(days=2),  # Stale
        )

    @pytest.fixture
    def mock_pypi_update(self):
        # Mock the function that updates the package from PyPI
        with patch(
            "package.management.commands.package_updater2.update_package_from_pypi"
        ) as m:

            def side_effect(package, **kwargs):
                # Simulate changes made by the function
                package.pypi_downloads = 5000
                package.latest_version = Version.objects.create(
                    package=package, number="1.0.0"
                )
                return package

            m.side_effect = side_effect
            yield m

    @pytest.fixture
    def mock_repo(self):
        # Mock the repo property on the Package model
        with patch("package.models.Package.repo", new_callable=MagicMock) as m:
            repo_handler = Mock()
            m.__get__ = Mock(return_value=repo_handler)

            def fetch_metadata(pkg, save=False):
                pkg.repo_watchers = 150
                pkg.repo_forks = 20

            repo_handler.fetch_metadata.side_effect = fetch_metadata
            yield repo_handler

    @pytest.fixture
    def mock_score(self):
        with patch(
            "package.management.commands.package_updater2.update_package_score"
        ) as m:

            def side_effect(package, save=False):
                package.score = 99
                return True

            m.side_effect = side_effect
            yield m

    def test_full_update_flow(
        self, runner, package, mock_pypi_update, mock_repo, mock_score
    ):
        # Pre-check
        assert package.pypi_downloads == 0
        assert package.repo_watchers == 0
        assert package.score == 0

        # Execute
        # We mock RateLimiter.wait to speed up tests
        with patch("package.management.commands.package_updater2.RateLimiter.wait"):
            result = runner.invoke(command, ["--all", "--chunk-size", "10"])

        assert result.exit_code == 0

        # Verify DB state (flush_updates should have saved the changes)
        package.refresh_from_db()
        assert package.pypi_downloads == 5000
        assert package.repo_watchers == 150
        assert package.score == 99
        assert package.latest_version is not None
        assert package.latest_version_number == "1.0.0"

        # Verify calls
        mock_pypi_update.assert_called_once()
        mock_repo.fetch_metadata.assert_called_once()
        mock_score.assert_called_once()
