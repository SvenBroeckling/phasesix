from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("plots", "0009_alter_plotelement_options_plotelement_ordering"),
        ("characters", "0031_character_cloned_from"),
    ]

    operations = [
        migrations.AddField(
            model_name="character",
            name="plot_campaign",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=models.deletion.SET_NULL,
                related_name="plot_npc_set",
                to="plots.plot",
                verbose_name="Plot Campaign",
            ),
        ),
    ]
