# Generated by Django 4.1.10 on 2023-08-12 00:15

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("characters", "0002_initial"),
        ("magic", "0003_alter_basespell_homebrew_campaign"),
    ]

    operations = [
        migrations.AddField(
            model_name="basespell",
            name="homebrew_character",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="homebrew_%(app_label)s_%(class)s_set",
                to="characters.character",
                verbose_name="homebrew character",
            ),
        ),
    ]
