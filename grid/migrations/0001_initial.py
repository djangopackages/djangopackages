# -*- coding: utf-8 -*-


from django.db import models, migrations
import core.fields
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('package', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Element',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', core.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', core.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
                ('text', models.TextField(help_text="\nLinebreaks are turned into 'br' tags<br />\nUrls are turned into links<br />\nYou can use just 'check', 'yes', 'good' to place a checkmark icon.<br />\nYou can use 'bad', 'negative', 'evil', 'sucks', 'no' to place a negative icon.<br />\nPlus just '+' or '-' signs can be used but cap at 3 multiples to protect layout<br/>\n\n", verbose_name='text', blank=True)),
            ],
            options={
                'ordering': ['-id'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Feature',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', core.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', core.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
                ('title', models.CharField(max_length=100, verbose_name='Title')),
                ('description', models.TextField(verbose_name='Description', blank=True)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Grid',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', core.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', core.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
                ('title', models.CharField(max_length=100, verbose_name='Title')),
                ('slug', models.SlugField(help_text='Slugs will be lowercased', unique=True, verbose_name='Slug')),
                ('description', models.TextField(help_text='Lines are broken and urls are urlized', verbose_name='Description', blank=True)),
                ('is_locked', models.BooleanField(default=False, help_text='Moderators can lock grid access', verbose_name='Is Locked')),
                ('header', models.BooleanField(default=False, help_text='If checked then displayed on homepage header', verbose_name='Header tab?')),
            ],
            options={
                'ordering': ['title'],
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='GridPackage',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', core.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', core.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
                ('grid', models.ForeignKey(to='grid.Grid', on_delete=django.db.models.deletion.CASCADE)),
                ('package', models.ForeignKey(to='package.Package', on_delete=django.db.models.deletion.CASCADE)),
            ],
            options={
                'verbose_name': 'Grid Package',
                'verbose_name_plural': 'Grid Packages',
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='grid',
            name='packages',
            field=models.ManyToManyField(to='package.Package', through='grid.GridPackage'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='feature',
            name='grid',
            field=models.ForeignKey(to='grid.Grid', on_delete=django.db.models.deletion.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='element',
            name='feature',
            field=models.ForeignKey(to='grid.Feature', on_delete=django.db.models.deletion.CASCADE),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='element',
            name='grid_package',
            field=models.ForeignKey(to='grid.GridPackage', on_delete=django.db.models.deletion.CASCADE),
            preserve_default=True,
        ),
    ]
