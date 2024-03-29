# Generated by Django 4.2.9 on 2024-03-29 12:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0005_extrafields_squashed_0009_profile_extra_field_content_01_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='extra_field_content_01',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Extra field content 01'),
        ),
        migrations.AlterField(
            model_name='profile',
            name='extra_field_content_02',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Extra field content 02'),
        ),
        migrations.AlterField(
            model_name='profile',
            name='extra_field_content_03',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Extra field content 03'),
        ),
        migrations.AlterField(
            model_name='profile',
            name='extra_field_content_04',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='Extra field content 04'),
        ),
    ]
