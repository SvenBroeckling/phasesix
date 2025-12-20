from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("plots", "0010_alter_plotelement_type"),
        ("rules", "0020_alter_foe_resistances_alter_foe_weaknesses"),
    ]

    operations = [
        migrations.AddField(
            model_name="plotelement",
            name="foes",
            field=models.ManyToManyField(blank=True, to="rules.foe"),
        ),
    ]
