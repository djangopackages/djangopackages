# Generated by Django 4.2.9 on 2024-04-07 11:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0005_add_extrafields'),
    ]

    operations = [
        migrations.AlterField(
            model_name='extrafields',
            name='value',
            field=models.URLField(max_length=256),
        ),
    ]
