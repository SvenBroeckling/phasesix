import uuid

from django.db import migrations, models


def populate_foundry_tokens(apps, schema_editor):
    Campaign = apps.get_model("campaigns", "Campaign")
    for campaign in Campaign.objects.all():
        campaign.foundry_token = uuid.uuid4()
        campaign.save(update_fields=["foundry_token"])


class Migration(migrations.Migration):
    dependencies = [
        ("campaigns", "0032_remove_campaign_character_and_game_log_visibility")
    ]

    operations = [
        migrations.AddField(
            model_name="campaign",
            name="foundry_token",
            field=models.UUIDField(blank=True, editable=False, null=True),
        ),
        migrations.RunPython(populate_foundry_tokens, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="campaign",
            name="foundry_token",
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
    ]
