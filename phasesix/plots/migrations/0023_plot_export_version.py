from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("plots", "0022_alter_plot_ruleset_alter_plotelement_essential_npc_and_more")
    ]

    operations = [
        migrations.AddField(
            model_name="plot",
            name="export_version",
            field=models.PositiveBigIntegerField(default=1),
        )
    ]
