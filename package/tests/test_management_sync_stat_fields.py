import datetime

import pytest
from django.core.management import call_command
from django.utils import timezone
from model_bakery import baker

from package.models import Commit, Package, Version


@pytest.fixture
def package_with_stats(db, category):
    package = baker.make(
        Package,
        category=category,
        title="Stats Package",
        slug="stats-package",
        repo_url="https://github.com/stats/package",
        commit_count=0,
        last_commit_date=None,
        commits_over_52w=[],
        latest_version=None,
        supports_python3=False,
    )

    # Create some commits
    now = timezone.now()
    baker.make(Commit, package=package, commit_date=now - datetime.timedelta(days=1))
    baker.make(Commit, package=package, commit_date=now - datetime.timedelta(days=10))
    baker.make(
        Commit, package=package, commit_date=now - datetime.timedelta(days=400)
    )  # Older than 52 weeks

    # Create versions
    baker.make(
        Version,
        package=package,
        number="1.0.0",
        upload_time=now - datetime.timedelta(days=100),
        hidden=False,
        supports_python3=False,
    )
    v2 = baker.make(
        Version,
        package=package,
        number="2.0.0",
        upload_time=now - datetime.timedelta(days=10),
        hidden=False,
        supports_python3=True,
    )
    baker.make(
        Version,
        package=package,
        number="3.0.0beta",
        upload_time=now - datetime.timedelta(days=1),
        hidden=True,
    )  # Hidden

    return package, v2


def test_sync_package_stat_fields(package_with_stats):
    package, latest_v = package_with_stats

    call_command("sync_package_stat_fields")

    package.refresh_from_db()

    # Check Commit Stats
    assert package.commit_count == 3
    assert package.last_commit_date is not None
    # The last commit date should be the most recent one (now - 1 day)
    # We can check if it's close to now - 1 day, or just that it's updated.

    # Check commits_over_52w
    assert len(package.commits_over_52w) == 52
    # We expect some commits in recent weeks.
    # 1 day ago is week 0. 10 days ago is week 1.
    assert package.commits_over_52w[51] >= 1  # week 0 (reversed)
    assert package.commits_over_52w[50] >= 1  # week 1 (reversed)

    # Check Version Stats
    assert package.latest_version == latest_v
    assert package.supports_python3 is True


def test_sync_package_stat_fields_dry_run(package_with_stats):
    package, _ = package_with_stats

    call_command("sync_package_stat_fields", "--dry-run")

    package.refresh_from_db()

    assert package.commit_count == 0
    assert package.last_commit_date is None
    assert package.latest_version is None


def test_sync_package_stat_fields_with_args(package_with_stats):
    package, latest_v = package_with_stats
    other_package = baker.make(Package, slug="other-package")

    call_command("sync_package_stat_fields", f"--package-id={package.pk}")

    package.refresh_from_db()
    other_package.refresh_from_db()

    assert package.commit_count == 3
    assert other_package.commit_count == 0


def test_sync_package_stat_fields_no_versions(package_with_stats):
    package, _ = package_with_stats

    call_command("sync_package_stat_fields", "--no-versions")

    package.refresh_from_db()

    assert package.commit_count == 3
    assert package.latest_version is None


def test_sync_package_stat_fields_no_commits(package_with_stats):
    package, latest_v = package_with_stats

    call_command("sync_package_stat_fields", "--no-commits")

    package.refresh_from_db()

    assert package.commit_count == 0
    assert package.latest_version == latest_v
