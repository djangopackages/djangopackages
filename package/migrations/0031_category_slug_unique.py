"""Make Category.slug unique.

Nothing stopped two categories sharing a slug, which made get_or_create in
0029 and 0030 only as safe as the absence of a concurrent migrate. It is not
hypothetical: running the container's boot migrate alongside a manual one
applied 0030 twice a millisecond apart and left two "deployment" rows, and
django_migrations on production shows 0010 was applied twice back in 2021.

A duplicate is also enough to break recategorize_from_grids, which looks a
destination up with Category.objects.get(slug=...).

Production has no duplicates today, so the merge step below is a no-op there.
It exists so this does not fail on a database that does.
"""

from django.db import migrations, models


def merge_duplicate_slugs(apps, schema_editor):
    """Fold any duplicates into the oldest row before the constraint lands."""
    Category = apps.get_model("package", "Category")
    Package = apps.get_model("package", "Package")

    seen = {}
    for category in Category.objects.order_by("pk"):
        keeper = seen.get(category.slug)
        if keeper is None:
            seen[category.slug] = category
            continue
        Package.objects.filter(category=category).update(category=keeper)
        category.delete()


def noop(apps, schema_editor):
    """Dropping the constraint needs no data change."""


class Migration(migrations.Migration):
    dependencies = [
        ("package", "0030_deployment_category"),
    ]

    operations = [
        migrations.RunPython(merge_duplicate_slugs, noop),
        migrations.AlterField(
            model_name="category",
            name="slug",
            field=models.SlugField(unique=True, verbose_name="slug"),
        ),
    ]
