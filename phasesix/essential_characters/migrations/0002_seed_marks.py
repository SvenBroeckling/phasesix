from django.db import migrations

from essential_characters.definitions import ANCESTRIES, BONDS, PATHS


def seed_marks(apps, schema_editor):
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


class Migration(migrations.Migration):
    dependencies = [("essential_characters", "0001_initial")]
    operations = [migrations.RunPython(seed_marks, migrations.RunPython.noop)]
