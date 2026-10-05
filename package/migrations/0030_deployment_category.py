"""Adds the Deployment category from #1135.

Same shape as 0029: get_or_create on the slug, and a reverse that only
removes a category nothing is filed under.
"""

from django.db import migrations

CATEGORY = {
    "slug": "deployment",
    "title": "Deployment",
    "title_plural": "Deployment",
    "description": (
        "Tools for getting a Django project onto a server and keeping it "
        "running: deploy scripts, WSGI and ASGI servers, and build recipes."
    ),
    "show_pypi": True,
}


def add_category(apps, schema_editor):
    Category = apps.get_model("package", "Category")
    Category.objects.get_or_create(
        slug=CATEGORY["slug"],
        defaults={key: value for key, value in CATEGORY.items() if key != "slug"},
    )


def remove_category(apps, schema_editor):
    Category = apps.get_model("package", "Category")
    Package = apps.get_model("package", "Package")

    row = Category.objects.filter(slug=CATEGORY["slug"]).first()
    if row and not Package.objects.filter(category=row).exists():
        row.delete()


class Migration(migrations.Migration):
    dependencies = [
        ("package", "0029_developer_tools_category"),
    ]

    operations = [
        migrations.RunPython(add_category, remove_category),
    ]
