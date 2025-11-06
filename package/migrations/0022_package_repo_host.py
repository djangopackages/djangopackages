from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("package", "0021_package_favorite_count"),
    ]

    operations = [
        migrations.AddField(
            model_name="package",
            name="repo_host",
            field=models.CharField(
                blank=True,
                choices=[
                    ("", "Auto-detect"),
                    ("bitbucket", "Bitbucket"),
                    ("github", "GitHub"),
                    ("gitlab", "GitLab"),
                    ("codeberg", "Codeberg"),
                    ("forgejo", "Forgejo"),
                ],
                default="",
                help_text="Select the hosting service when auto-detection cannot determine it.",
                max_length=30,
                verbose_name="Repo host",
            ),
        ),
    ]
