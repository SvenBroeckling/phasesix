# Generated by Django 4.1.10 on 2023-08-17 17:41

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("rules", "0001_initial"),
        ("armory", "0004_item_homebrew_character_riotgear_homebrew_character_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="item",
            name="extensions",
            field=models.ManyToManyField(blank=True, to="rules.extension"),
        ),
        migrations.AlterField(
            model_name="riotgear",
            name="extensions",
            field=models.ManyToManyField(blank=True, to="rules.extension"),
        ),
        migrations.AlterField(
            model_name="weapon",
            name="extensions",
            field=models.ManyToManyField(blank=True, to="rules.extension"),
        ),
        migrations.AlterField(
            model_name="weaponmodification",
            name="extensions",
            field=models.ManyToManyField(blank=True, to="rules.extension"),
        ),
    ]
