"""Recompute every Package.score on the 0 to 100 scale (#1563).

A data migration rather than a command to run by hand, so the deploy that
changes the formula also changes the stored numbers the grids sort and
cut on. Takes about a second for six thousand packages.
"""

from django.db import migrations


def rescore(apps, schema_editor):
    from package.scoring import ScoreInputs, calculate_score

    Package = apps.get_model("package", "Package")
    changed = []
    packages = Package.objects.select_related("latest_version").only(
        "pk",
        "score",
        "repo_watchers",
        "pypi_downloads",
        "last_commit_date",
        "date_deprecated",
        "date_repo_archived",
        "latest_version__upload_time",
    )
    for package in packages.iterator(chunk_size=1000):
        score = calculate_score(ScoreInputs.from_package(package))
        if package.score != score:
            package.score = score
            changed.append(package)
    Package.objects.bulk_update(changed, ["score"], batch_size=500)


class Migration(migrations.Migration):
    dependencies = [
        ("package", "0035_package_tags"),
    ]

    operations = [
        migrations.RunPython(rescore, migrations.RunPython.noop),
    ]
