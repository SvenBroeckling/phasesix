# Generated by Django 4.1.10 on 2023-08-27 16:56

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("worlds", "0003_world_brand_logo_world_brand_name_and_more"),
    ]

    operations = [
        migrations.RenameField(
            model_name="world",
            old_name="brand_name",
            new_name="brand_name_de",
        ),
        migrations.AddField(
            model_name="world",
            name="brand_name_en",
            field=models.CharField(
                blank=True, max_length=80, null=True, verbose_name="Brand name"
            ),
        ),
    ]
