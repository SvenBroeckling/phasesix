# Generated by Django 4.1.10 on 2023-08-11 16:47

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("campaigns", "0004_campaign_created_at"),
        ("pantheon", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="entity",
            name="homebrew_campaign",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="homebrew_%(app_label)s_%(class)s_set",
                to="campaigns.campaign",
                verbose_name="homebrew campaign",
            ),
        ),
        migrations.AlterField(
            model_name="entity",
            name="keep_as_homebrew",
            field=models.BooleanField(
                default=False,
                help_text="This was not accepted as general spell and is kept as homebrew.",
                verbose_name="keep as homebrew",
            ),
        ),
        migrations.AlterField(
            model_name="priestaction",
            name="homebrew_campaign",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="homebrew_%(app_label)s_%(class)s_set",
                to="campaigns.campaign",
                verbose_name="homebrew campaign",
            ),
        ),
    ]
