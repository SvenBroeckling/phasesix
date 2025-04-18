# Generated by Django 5.1.5 on 2025-01-30 17:48

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("characters", "0005_characterattribute_modifier"),
        ("worlds", "0027_language_homebrew_campaign_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="CharacterLanguage",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("modifier", models.IntegerField(default=0, verbose_name="Modifier")),
                (
                    "character",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="characters.character",
                    ),
                ),
                (
                    "language",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="worlds.language",
                    ),
                ),
            ],
        ),
    ]
