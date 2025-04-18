# Generated by Django 4.1.10 on 2023-08-27 16:54

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("worlds", "0002_world_foe_overview_wiki_page"),
    ]

    operations = [
        migrations.AddField(
            model_name="world",
            name="brand_logo",
            field=models.ImageField(
                blank=True,
                max_length=256,
                null=True,
                upload_to="brand_logos",
                verbose_name="Brand Logo",
            ),
        ),
        migrations.AddField(
            model_name="world",
            name="brand_name",
            field=models.CharField(
                default="Phase Six", max_length=80, verbose_name="Brand name"
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="world",
            name="template_addon",
            field=models.CharField(
                default="tirakan", max_length=40, verbose_name="Template Suffix"
            ),
            preserve_default=False,
        ),
    ]
