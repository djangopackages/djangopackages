import pytest
from django.utils import timezone
from click.testing import CliRunner

from package.models import Package, Category
from package.management.commands.calculate_score import command


@pytest.mark.django_db
class TestCalculateScoreCommand:
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
            repo_watchers=100,
            last_commit_date=timezone.now(),
            score=0,
        )

    def test_calculate_score_update(self, runner, package):
        # Pre-check
        assert package.score == 0

        # Execute
        result = runner.invoke(command, [])

        # Verify
        assert result.exit_code == 0
        package.refresh_from_db()
        # 100 stars, committed today, nothing else known (see test_scores.py)
        assert package.score == 33

    def test_calculate_score_archived_loses_points(self, runner, package):
        package.date_repo_archived = timezone.now()
        package.score = 100
        package.save()

        runner.invoke(command, [])

        package.refresh_from_db()
        assert package.score == 16

    def test_min_watchers_filter(self, runner, category):
        p1 = Package.objects.create(
            title="P1",
            slug="p1",
            category=category,
            repo_watchers=100,
            last_commit_date=timezone.now(),
            repo_url="https://github.com/p1/p1",
        )
        p2 = Package.objects.create(
            title="P2",
            slug="p2",
            category=category,
            repo_watchers=10,
            last_commit_date=timezone.now(),
            repo_url="https://github.com/p2/p2",
        )

        runner.invoke(command, ["--min-watchers", "50"])

        p1.refresh_from_db()
        p2.refresh_from_db()
        assert p1.score == 33
        assert p2.score == 0  # Should not be updated

    def test_dry_run(self, runner, package):
        result = runner.invoke(command, ["--dry-run"])

        assert result.exit_code == 0
        assert "Would update" in result.output
        package.refresh_from_db()
        assert package.score == 0
