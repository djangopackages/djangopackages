import datetime

from django.utils import timezone
from model_bakery import baker

from package.models import Package
from package.scores import (
    UpdateResult,
    _calculate_score,
    update_package_score,
    update_package_scores_bulk,
)


def test_calculate_score_recent_python3():
    last_commit_date = timezone.now() - datetime.timedelta(days=10)
    score = _calculate_score(
        repo_watchers=100,
        last_commit_date=last_commit_date,
        supports_python3=True,
    )
    assert score == 100


def test_calculate_score_no_commit_date_and_no_python3():
    score = _calculate_score(
        repo_watchers=100,
        last_commit_date=None,
        supports_python3=False,
    )
    assert score == 60


def test_update_package_score_updates_when_changed(db, category):
    package = baker.make(
        Package,
        category=category,
        repo_url="https://github.com/test/score-updates",
        repo_watchers=100,
        supports_python3=True,
        last_commit_date=timezone.now(),
        score=0,
    )

    updated = update_package_score(package, save=True)

    assert updated is True
    package.refresh_from_db()
    assert package.score == 100

    updated_again = update_package_score(package, save=True)
    assert updated_again is False


def test_update_package_scores_bulk_updates_only_changed(db, category):
    package_unchanged = baker.make(
        Package,
        category=category,
        repo_url="https://github.com/test/score-unchanged",
        repo_watchers=50,
        supports_python3=True,
        last_commit_date=timezone.now(),
    )
    package_unchanged.score = _calculate_score(
        repo_watchers=package_unchanged.repo_watchers,
        last_commit_date=package_unchanged.last_commit_date,
        supports_python3=package_unchanged.supports_python3,
    )
    package_unchanged.save(update_fields=["score"])

    package_changed = baker.make(
        Package,
        category=category,
        repo_url="https://github.com/test/score-changed",
        repo_watchers=80,
        supports_python3=True,
        last_commit_date=timezone.now(),
        score=0,
    )

    progress = []

    def progress_callback(processed: int, total: int):
        progress.append((processed, total))

    result = update_package_scores_bulk(
        Package.objects.filter(pk__in=[package_unchanged.pk, package_changed.pk]),
        batch_size=1,
        progress_callback=progress_callback,
    )

    assert result.updated_count == 1
    assert result.total_count == 2
    assert result.skipped_count == 1
    assert progress[-1][0] == 2

    package_changed.refresh_from_db()
    assert package_changed.score == 80


def test_update_result_success_rate():
    result = UpdateResult(updated_count=2, total_count=4, skipped_count=2)
    assert result.success_rate == 50.0
