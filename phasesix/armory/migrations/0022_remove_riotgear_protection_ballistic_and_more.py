# Generated by Django 5.1.2 on 2024-11-02 17:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("armory", "0021_remove_protectiontype_rules_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="riotgear",
            name="protection_ballistic",
        ),
        migrations.AddField(
            model_name="riotgear",
            name="shield_cover",
            field=models.IntegerField(default=0, verbose_name="shield cover"),
        ),
    ]
