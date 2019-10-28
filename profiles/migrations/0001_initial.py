# -*- coding: utf-8 -*-


from django.db import models, migrations
import django.utils.timezone
from django.conf import settings
import core.fields


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Profile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', core.fields.CreationDateTimeField(default=django.utils.timezone.now, verbose_name='created', editable=False, blank=True)),
                ('modified', core.fields.ModificationDateTimeField(default=django.utils.timezone.now, verbose_name='modified', editable=False, blank=True)),
                ('github_account', models.CharField(max_length=40, null=True, verbose_name='Github account', blank=True)),
                ('github_url', models.CharField(verbose_name='Github account', max_length=100, null=True, editable=False, blank=True)),
                ('bitbucket_url', models.CharField(max_length=100, null=True, verbose_name='Bitbucket account', blank=True)),
                ('google_code_url', models.CharField(max_length=100, null=True, verbose_name='Google Code account', blank=True)),
                ('email', models.EmailField(max_length=75, null=True, verbose_name='Email', blank=True)),
                ('user', models.OneToOneField(to=settings.AUTH_USER_MODEL, on_delete=django.db.models.deletion.CASCADE)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
    ]
