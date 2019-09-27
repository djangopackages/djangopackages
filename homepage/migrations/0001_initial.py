# -*- coding: utf-8 -*-


from django.db import models, migrations
import core.fields
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('grid', '0001_initial'),
        ('package', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Dpotw',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', core.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', core.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
                ('start_date', models.DateField(verbose_name='Start Date')),
                ('end_date', models.DateField(verbose_name='End Date')),
                ('package', models.ForeignKey(to='package.Package', on_delete=django.db.models.deletion.CASCADE)),
            ],
            options={
                'ordering': ('-start_date', '-end_date'),
                'get_latest_by': 'created',
                'verbose_name': 'Django Package of the Week',
                'verbose_name_plural': 'Django Packages of the Week',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Gotw',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', core.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', core.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
                ('start_date', models.DateField(verbose_name='Start Date')),
                ('end_date', models.DateField(verbose_name='End Date')),
                ('grid', models.ForeignKey(to='grid.Grid', on_delete=django.db.models.deletion.CASCADE)),
            ],
            options={
                'ordering': ('-start_date', '-end_date'),
                'get_latest_by': 'created',
                'verbose_name': 'Grid of the Week',
                'verbose_name_plural': 'Grids of the Week',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='PSA',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', core.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', core.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
                ('body_text', models.TextField(null=True, verbose_name='PSA Body Text', blank=True)),
            ],
            options={
                'ordering': ('-created',),
                'get_latest_by': 'created',
                'verbose_name': 'Public Service Announcement',
                'verbose_name_plural': 'Public Service Announcements',
            },
            bases=(models.Model,),
        ),
    ]
