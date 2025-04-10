# Generated by Django 4.1.11 on 2023-09-14 18:32

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("worlds", "0010_remove_world_template_addon_world_index_template"),
    ]

    operations = [
        migrations.AddField(
            model_name="world",
            name="scss_file",
            field=models.CharField(
                choices=[
                    ("theme/phasesix.scss", "theme/phasesix.scss"),
                    ("theme/tirakan.scss", "theme/tirakan.scss"),
                    ("theme/nexus.scss", "theme/nexus.scss"),
                ],
                default="theme/phasesix.scss",
                max_length=40,
                verbose_name="SCSS File",
            ),
        ),
    ]
