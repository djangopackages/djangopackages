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
                help_text="How many PyPI projects list this one as a requirement.",
                null=True,
                verbose_name="PyPI dependents",
            ),
        ),
        migrations.AddField(
            model_name="package",
            name="pypi_dependencies",
            field=models.IntegerField(
                blank=True,
                help_text="How many projects this one requires, extras excluded.",
                null=True,
                verbose_name="PyPI dependencies",
            ),
        ),
        migrations.AddField(
            model_name="package",
            name="pypi_scorecard",
            field=models.FloatField(
                blank=True, null=True, verbose_name="OpenSSF Scorecard"
            ),
        ),
        migrations.AddField(
            model_name="package",
            name="pypi_has_vulnerabilities",
            field=models.BooleanField(
                blank=True, null=True, verbose_name="Known vulnerabilities on PyPI"
            ),
        ),
        migrations.AddField(
            model_name="package",
            name="pypi_data_synced_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
