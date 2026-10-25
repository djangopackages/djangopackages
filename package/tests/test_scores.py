from django.utils import timezone
from model_bakery import baker

from package.models import Package
from package.scores import (
    UpdateResult,
    calculate_score,
    update_package_score,
    update_package_scores_bulk,
)

# 100 stars, committed today, nothing else known: not deprecated (20),
# commit in the last 3 months (20), watchers (20) of 160, scaled to 100.
# The rules themselves are covered in searchv3/tests/test_score_rules.py.
FRESH_100_STARS = 33


def test_update_package_score_archived_loses_the_deprecated_rule(db, category):
    package = baker.make(
        Package,
        category=category,
        repo_url="https://github.com/test/score-archived",
        repo_watchers=100,
        last_commit_date=timezone.now(),
        date_repo_archived=timezone.now(),
        score=100,
    )

    assert update_package_score(package, save=True) is True
    package.refresh_from_db()
    # Fresh with 100 stars is 33; archived forfeits the 20 "not deprecated" points.
    assert package.score == 16


def test_update_package_score_updates_when_changed(db, category):
    package = baker.make(
        Package,
        category=category,
        repo_url="https://github.com/test/score-updates",
        repo_watchers=100,
        last_commit_date=timezone.now(),
        score=0,
    )

    updated = update_package_score(package, save=True)

    assert updated is True
    package.refresh_from_db()
    assert package.score == FRESH_100_STARS

    updated_again = update_package_score(package, save=True)
    assert updated_again is False


def test_update_package_scores_bulk_updates_only_changed(db, category):
    package_unchanged = baker.make(
        Package,
        category=category,
        repo_url="https://github.com/test/score-unchanged",
        repo_watchers=50,
        last_commit_date=timezone.now(),
    )
    package_unchanged.score = calculate_score(package_unchanged)
    package_unchanged.save(update_fields=["score"])

    package_changed = baker.make(
        Package,
        category=category,
        repo_url="https://github.com/test/score-changed",
        repo_watchers=80,
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
    assert package_changed.score == calculate_score(package_changed)
    assert package_changed.score > 0


def test_update_result_success_rate():
    result = UpdateResult(updated_count=2, total_count=4, skipped_count=2)
    assert result.success_rate == 50.0
