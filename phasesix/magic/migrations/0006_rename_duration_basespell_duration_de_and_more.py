# Generated by Django 5.1 on 2024-08-30 20:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("magic", "0005_basespell_duration_basespell_needs_concentration"),
    ]

    operations = [
        migrations.RenameField(
            model_name="basespell",
            old_name="duration",
            new_name="duration_de",
        ),
        migrations.AddField(
            model_name="basespell",
            name="duration_en",
            field=models.CharField(
                blank=True, max_length=40, null=True, verbose_name="duration"
            ),
        ),
    ]
