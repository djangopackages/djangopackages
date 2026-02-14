from django.utils import timezone
from model_bakery import baker

from searchv2.rules import RecentReleaseRule


def test_recent_release_rule_handles_null_upload_time(db):
    category = baker.make("package.Category")
    package = baker.make("package.Package", category=category)
    version = baker.make("package.Version", package=package, upload_time=None)
    package.latest_version = version
    package.save(update_fields=["latest_version"])

    result = RecentReleaseRule().check(package=package)

    assert result.score == 0
    assert result.message == "No release data found for the package."


def test_recent_release_rule_scores_recent_release(db):
    category = baker.make("package.Category")
    package = baker.make("package.Package", category=category)
    version = baker.make(
        "package.Version",
        package=package,
        upload_time=timezone.now() - timezone.timedelta(days=30),
    )
    package.latest_version = version
    package.save(update_fields=["latest_version"])

    result = RecentReleaseRule().check(package=package)

    assert result.score == RecentReleaseRule().max_score
    assert result.message == "Last release is less than a year old."
