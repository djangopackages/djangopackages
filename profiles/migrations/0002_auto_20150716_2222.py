from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("profiles", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="profile",
            name="email",
            field=models.EmailField(
                max_length=254, null=True, verbose_name="Email", blank=True
            ),
        ),
    ]
