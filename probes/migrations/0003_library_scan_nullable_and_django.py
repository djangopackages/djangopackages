from django.db import migrations, models


def add_django(apps, schema_editor):
    """Django is the one library we always scan for, so it starts on."""
    Library = apps.get_model("probes", "Library")
    Library.objects.update_or_create(
        pypi_name="django",
        defaults={
            "import_name": "django",
            "also_imports": [],
            "source": "manual",
            "scan": True,
            "notes": "The library every scan counts; the rest are opt in.",
        },
    )


def remove_django(apps, schema_editor):
    apps.get_model("probes", "Library").objects.filter(pypi_name="django").delete()


class Migration(migrations.Migration):
    dependencies = [("probes", "0002_library")]

    operations = [
        migrations.AlterField(
            model_name="library",
            name="scan",
            field=models.BooleanField(
                blank=True,
                default=None,
                help_text=(
                    "Toggle on to have scans count this library's usage as well as "
                    "Django's. Null means nobody has decided, which reads as off: "
                    "every library added here is counted in every file of every "
                    "checkout, so it is opt in."
                ),
                null=True,
                verbose_name="scan for this library",
            ),
        ),
        migrations.RunPython(add_django, remove_django),
    ]
