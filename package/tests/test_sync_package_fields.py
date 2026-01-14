import datetime

from django.core.management import call_command
from django.utils.timezone import make_aware
from model_bakery import baker

from package.models import Commit, Package, Version


def _parse_histogram(value: str) -> list[int]:
    parts = [p for p in value.split(",") if p != ""]
    return [int(p) for p in parts]


def test_sync_package_fields_updates_commit_rollups(db, category):
    package = baker.make(
        Package,
        category=category,
        repo_url="https://github.com/example/repo",
        slug="example-repo",
        title="Example Repo",
        commits_over_52="",
        last_commit_date=None,
    )

    now_dt = make_aware(datetime.datetime(2022, 2, 20, 2, 22))

    # Two commits within the last 52 weeks
    baker.make(Commit, package=package, commit_date=now_dt)
    baker.make(Commit, package=package, commit_date=now_dt - datetime.timedelta(days=7))

    # One commit outside the 52-week window (should not affect histogram)
    baker.make(
        Commit,
        package=package,
        commit_date=now_dt - datetime.timedelta(days=370),
    )

    call_command("sync_package_fields", "--no-versions", "--slug", package.slug)

    package.refresh_from_db()

    assert package.last_commit_date == datetime.date(2022, 2, 20)

    hist = _parse_histogram(package.commits_over_52)
    assert len(hist) == 52

    # Stored as oldest -> newest; newest week is the last element.
    assert hist[-1] == 1  # 0-6 days ago
    assert hist[-2] == 1  # 7-13 days ago
    assert sum(hist) == 2


def test_sync_package_fields_updates_latest_version(db, category):
    package = baker.make(
        Package,
        category=category,
        repo_url="https://github.com/example/versions",
        slug="example-versions",
        title="Example Versions",
        latest_version=None,
    )

    v1 = baker.make(
        Version,
        package=package,
        number="1.0.0",
        hidden=False,
        upload_time=make_aware(datetime.datetime(2022, 1, 1, 0, 0)),
    )
    v2 = baker.make(
        Version,
        package=package,
        number="1.1.0",
        hidden=False,
        upload_time=make_aware(datetime.datetime(2022, 2, 1, 0, 0)),
    )

    # Hidden should not be selected as the latest.
    baker.make(
        Version,
        package=package,
        number="9.9.9",
        hidden=True,
        upload_time=make_aware(datetime.datetime(2022, 12, 1, 0, 0)),
    )

    call_command("sync_package_fields", "--no-commits", "--slug", package.slug)
    package.refresh_from_db()

    assert package.latest_version_id == v2.id
    assert package.latest_version_id != v1.id
