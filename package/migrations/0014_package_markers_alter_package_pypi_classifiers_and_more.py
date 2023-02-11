# Generated by Django 4.0.3 on 2022-03-19 20:23

import django_better_admin_arrayfield.models.fields
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("package", "0013_package_last_exception_package_last_exception_at_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="package",
            name="markers",
            field=django_better_admin_arrayfield.models.fields.ArrayField(
                base_field=models.CharField(max_length=100),
                blank=True,
                null=True,
                size=None,
            ),
        ),
        migrations.AlterField(
            model_name="package",
            name="pypi_classifiers",
            field=django_better_admin_arrayfield.models.fields.ArrayField(
                base_field=models.CharField(max_length=100),
                blank=True,
                null=True,
                size=None,
            ),
        ),
        migrations.AlterField(
            model_name="package",
            name="pypi_licenses",
            field=django_better_admin_arrayfield.models.fields.ArrayField(
                base_field=models.CharField(max_length=100),
                blank=True,
                null=True,
                size=None,
            ),
        ),
        migrations.AlterField(
            model_name="version",
            name="licenses",
            field=django_better_admin_arrayfield.models.fields.ArrayField(
                base_field=models.CharField(max_length=100, verbose_name="licenses"),
                blank=True,
                help_text="Comma separated list of licenses.",
                null=True,
                size=None,
            ),
        ),
    ]
