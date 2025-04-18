# Generated by Django 5.1 on 2024-08-21 19:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("armory", "0005_alter_item_extensions_alter_riotgear_extensions_and_more"),
    ]

    operations = [
        migrations.RenameField(
            model_name="currencymapunit",
            old_name="name",
            new_name="name_de",
        ),
        migrations.AddField(
            model_name="currencymapunit",
            name="name_en",
            field=models.CharField(
                blank=True, max_length=20, null=True, verbose_name="name"
            ),
        ),
        migrations.AddField(
            model_name="currencymapunit",
            name="value",
            field=models.DecimalField(
                decimal_places=2,
                default=1,
                help_text="Value in relation to the common unit.",
                max_digits=6,
                verbose_name="value",
            ),
        ),
    ]
