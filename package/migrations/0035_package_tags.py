from django.db import migrations, models

# The curated lists whose checkouts we keep so their entries can be read
# back. Add a slug here (and a package on the site) to track another one.
AWESOME_LISTS = [
    "awesome-django",
    "awesome-django-rest-framework",
    "awesome-wagtail",
]


def tag_awesome_lists(apps, schema_editor):
    Package = apps.get_model("package", "Package")
    for package in Package.objects.filter(slug__in=AWESOME_LISTS):
        if "awesome-list" not in package.tags:
            package.tags = [*package.tags, "awesome-list"]
            package.save(update_fields=["tags"])


class Migration(migrations.Migration):
    dependencies = [
        ("package", "0034_package_repo_license"),
    ]

    operations = [
        migrations.AddField(
            model_name="package",
            name="tags",
            field=models.JSONField(
                blank=True,
                default=list,
                help_text='Internal labels, a list of PackageTag values. ["awesome-list"] marks a package as a curated list whose checkout we keep even though it has no PyPI release.',
                verbose_name="Tags",
            ),
        ),
        migrations.RunPython(tag_awesome_lists, migrations.RunPython.noop),
    ]
