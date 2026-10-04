"""Adds the categories recategorize_from_grids files packages into (#1135).

Developer Tools is new. Starter Projects is not: it was created by hand in the
admin in November, so it exists in production and in no other database. Both
go in here as data so a local or test database can run the command at all.

get_or_create on the slug, so this is a no-op against production where Starter
Projects already exists rather than a second row with the same slug.
"""

from django.db import migrations

CATEGORIES = [
    {
        "slug": "developer-tools",
        "title": "Developer Tool",
        "title_plural": "Developer Tools",
        "description": (
            "Tools you run against a Django project rather than install into "
            "it: linters, formatters, test helpers, profilers, and "
            "documentation tooling."
        ),
        "show_pypi": True,
    },
    {
        "slug": "starter-projects",
        "title": "Starter Project",
        "title_plural": "Starter Projects",
        "description": (
            "Pre-built Django setups that provide a ready-to-use project "
            "structure, common settings, and optional integrations to help "
            "you start new projects quickly."
        ),
        "show_pypi": False,
    },
]


def add_categories(apps, schema_editor):
    Category = apps.get_model("package", "Category")
    for category in CATEGORIES:
        Category.objects.get_or_create(
            slug=category["slug"],
            defaults={key: value for key, value in category.items() if key != "slug"},
        )


def remove_categories(apps, schema_editor):
    """Only removes a category nothing is filed under, so reversing this does
    not orphan packages somebody moved into it.
    """
    Category = apps.get_model("package", "Category")
    Package = apps.get_model("package", "Package")

    for category in CATEGORIES:
        row = Category.objects.filter(slug=category["slug"]).first()
        if row and not Package.objects.filter(category=row).exists():
            row.delete()


class Migration(migrations.Migration):
    dependencies = [
        ("package", "0028_alter_package_documentation_url"),
    ]

    operations = [
        migrations.RunPython(add_categories, remove_categories),
    ]
