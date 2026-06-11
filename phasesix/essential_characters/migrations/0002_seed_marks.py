from django.db import migrations

from essential_characters.catalog import ARMOR, WEAPONS
from essential_characters.definitions import ANCESTRIES, BONDS, PATHS


def seed_essential_data(apps, schema_editor):
    extension_identifiers = ("middleages", "magic", "tirakan")

    for model_name, definitions in (
        ("EssentialAncestry", ANCESTRIES),
        ("EssentialPath", PATHS),
        ("EssentialBond", BONDS),
    ):
        model = apps.get_model("essential_characters", model_name)
        for definition in definitions:
            model.objects.update_or_create(
                name_de=definition["name_de"],
                defaults=definition,
            )

    for model_name, definitions, fields in (
        ("Weapon", WEAPONS, ("damage", "range", "grip", "properties")),
        ("RiotGear", ARMOR, ("protection", "load", "sealing", "properties")),
    ):
        model = apps.get_model("armory", model_name)
        model.objects.filter(
            extensions__identifier__in=extension_identifiers
        ).update(essential_enabled=True)
        for name, *values in definitions:
            matches = model.objects.filter(name_de=name)
            if matches.count() == 1:
                resource = matches.get()
                resource.essential_enabled = True
                for field, value in zip(fields, values):
                    setattr(resource, f"essential_{field}", value)
                resource.save()


class Migration(migrations.Migration):
    dependencies = [("essential_characters", "0001_initial")]
    operations = [
        migrations.RunPython(seed_essential_data, migrations.RunPython.noop),
    ]
