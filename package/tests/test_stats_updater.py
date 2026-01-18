import datetime

import pytest
from django.utils import timezone
from model_bakery import baker

from package.models import Commit, Package, Version
from package.stats_updater import (
    UpdateResult,
    _aggregate_commit_stats,
    update_commit_stats_bulk,
    update_latest_version_bulk,
    update_package_commit_stats,
    update_package_latest_version,
    update_package_stat_fields,
    update_package_stat_fields_bulk,
)


def test_aggregate_commit_stats_histogram(db, category):
    package = baker.make(
        Package,
        category=category,
        repo_url="https://github.com/test/commit-stats",
        commits_over_52w=[],
        last_commit_date=None,
    )

    now = timezone.now()
    baker.make(Commit, package=package, commit_date=now - datetime.timedelta(days=3))
    baker.make(Commit, package=package, commit_date=now - datetime.timedelta(days=10))
    baker.make(Commit, package=package, commit_date=now - datetime.timedelta(days=370))

    stats = _aggregate_commit_stats([package.pk])

    expected_last_commit = now - datetime.timedelta(days=3)
    assert stats.last_commit_date[package.pk].date() == expected_last_commit.date()
    histogram = stats.weekly_histogram[package.pk]
    assert len(histogram) == 52
    assert histogram[-1] == 1
    assert histogram[-2] == 1
    assert sum(histogram) == 2


def test_update_package_latest_version_no_versions(db, category):
    package = baker.make(
        Package,
        category=category,
        repo_url="https://github.com/test/latest-version-none",
        latest_version=None,
    )

    updated = update_package_latest_version(package, save=True)

    assert updated is False
    package.refresh_from_db()
    assert package.latest_version is None


def test_update_package_latest_version_updates_supports_python3(db, category):
    package = baker.make(
        Package,
        category=category,
        repo_url="https://github.com/test/latest-version",
        latest_version=None,
    )

    baker.make(
        Version,
        package=package,
        number="0.9.0",
        hidden=False,
        supports_python3=False,
        upload_time=timezone.now() - datetime.timedelta(days=10),
    )
    latest = baker.make(
        Version,
        package=package,
        number="1.0.0",
        hidden=False,
        supports_python3=True,
        upload_time=timezone.now() - datetime.timedelta(days=1),
    )
    baker.make(
        Version,
        package=package,
        number="9.9.9",
        hidden=True,
        supports_python3=False,
        upload_time=timezone.now(),
    )

    updated = update_package_latest_version(package, save=True)

    assert updated is True
    package.refresh_from_db()
    assert package.latest_version_id == latest.id
    assert package.supports_python3 is True


def test_update_package_commit_stats_updates_fields(db, category):
    package = baker.make(
        Package,
        category=category,
        repo_url="https://github.com/test/commit-stats-update",
        commits_over_52w=[1],
        last_commit_date=None,
    )
    baker.make(Commit, package=package, commit_date=timezone.now())

    updated = update_package_commit_stats(package, save=True)

    assert updated is True
    package.refresh_from_db()
    assert package.last_commit_date is not None
    assert len(package.commits_over_52w) == 52


def test_update_package_stat_fields_combined(db, category):
    package = baker.make(
        Package,
        category=category,
        repo_url="https://github.com/test/stat-fields",
        commits_over_52w=[],
        last_commit_date=None,
        latest_version=None,
    )
    baker.make(Commit, package=package, commit_date=timezone.now())
    latest = baker.make(
        Version,
        package=package,
        number="1.0.0",
        hidden=False,
        supports_python3=True,
        upload_time=timezone.now(),
    )

    result = update_package_stat_fields(
        package, update_version=True, update_commits=True, save=True
    )

    assert result == {"version_updated": True, "commits_updated": True}
    package.refresh_from_db()
    assert package.latest_version_id == latest.id
    assert package.last_commit_date is not None


def test_update_latest_version_bulk_validation(db):
    with pytest.raises(ValueError):
        update_latest_version_bulk(Package.objects.none(), batch_size=0)


def test_update_commit_stats_bulk_validation(db):
    with pytest.raises(ValueError):
        update_commit_stats_bulk(Package.objects.none(), batch_size=0)


def test_update_package_stat_fields_bulk_keys(db, category):
    package = baker.make(
        Package,
        category=category,
        repo_url="https://github.com/test/stat-fields-bulk",
    )
    baker.make(Commit, package=package, commit_date=timezone.now())

    results = update_package_stat_fields_bulk(
        Package.objects.filter(pk=package.pk),
        batch_size=1,
        update_version=False,
        update_commits=True,
    )

    assert "commits" in results
    assert "version" not in results
    assert isinstance(results["commits"], UpdateResult)
