from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("package", "0035_package_tags"),
    ]

    operations = [
        migrations.AddField(
            model_name="package",
            name="pypi_dependents",
            field=models.IntegerField(
                blank=True,
                help_text="PyPI projects that depend on the current release, directly or through another dependency, according to deps.dev.",
                null=True,
                verbose_name="PyPI dependents",
            ),
        ),
        migrations.AddField(
            model_name="package",
            name="pypi_direct_dependents",
            field=models.IntegerField(
                blank=True, null=True, verbose_name="PyPI direct dependents"
            ),
        ),
        migrations.AddField(
            model_name="package",
            name="pypi_dependents_synced_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
