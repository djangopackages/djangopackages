# -*- coding: utf-8 -*-


from django.db import models, migrations
import django.utils.timezone
import core.fields


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='SearchV2',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', core.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', core.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
                ('weight', models.IntegerField(default=0, verbose_name='Weight')),
                ('item_type', models.CharField(max_length=40, verbose_name='Item Type', choices=[('package', 'Package'), ('grid', 'Grid')])),
                ('title', models.CharField(max_length='100', verbose_name='Title', db_index=True)),
                ('title_no_prefix', models.CharField(max_length='100', verbose_name='No Prefix Title', db_index=True)),
                ('slug', models.SlugField(verbose_name='Slug')),
                ('slug_no_prefix', models.SlugField(verbose_name='No Prefix Slug')),
                ('clean_title', models.CharField(max_length='100', verbose_name='Clean title with no crud', db_index=True)),
                ('description', models.TextField(verbose_name='Repo Description', blank=True)),
                ('category', models.CharField(max_length=50, verbose_name='Category', blank=True)),
                ('absolute_url', models.CharField(max_length='255', verbose_name='Absolute URL')),
                ('repo_watchers', models.IntegerField(default=0, verbose_name='repo watchers')),
                ('repo_forks', models.IntegerField(default=0, verbose_name='repo forks')),
                ('pypi_downloads', models.IntegerField(default=0, verbose_name='Pypi downloads')),
                ('usage', models.IntegerField(default=0, verbose_name='Number of users')),
                ('participants', models.TextField(help_text='List of collaborats/participants on the project', verbose_name='Participants', blank=True)),
                ('last_committed', models.DateTimeField(null=True, verbose_name='Last commit', blank=True)),
                ('last_released', models.DateTimeField(null=True, verbose_name='Last release', blank=True)),
            ],
            options={
                'ordering': ['-weight'],
                'verbose_name_plural': 'SearchV2s',
            },
            bases=(models.Model,),
        ),
    ]
