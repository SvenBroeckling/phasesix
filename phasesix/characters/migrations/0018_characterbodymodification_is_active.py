# Generated by Django 5.1.7 on 2025-04-15 19:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("characters", "0017_characterbodymodification_charges_used"),
    ]

    operations = [
        migrations.AddField(
            model_name="characterbodymodification",
            name="is_active",
            field=models.BooleanField(default=True, verbose_name="is active"),
        ),
    ]
