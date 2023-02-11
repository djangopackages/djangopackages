from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("package", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="package",
            name="repo_watchers",
            field=models.IntegerField(default=0, verbose_name="Stars"),
        ),
    ]
