# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('searchv2', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='searchv2',
            name='repo_watchers',
            field=models.IntegerField(default=0, verbose_name='Stars'),
        ),
    ]
