# Generated by Django 5.1.7 on 2025-04-14 11:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("body_modifications", "0008_auto_20250414_1101"),
    ]

    operations = [
        migrations.AddField(
            model_name="socketlocation",
            name="identifier",
            field=models.CharField(
                default="", max_length=30, verbose_name="identifier"
            ),
            preserve_default=False,
        ),
    ]
