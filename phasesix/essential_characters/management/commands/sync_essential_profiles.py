from django.core.management.base import BaseCommand
from armory.models import Weapon, RiotGear
from essential_characters.catalog import ARMOR, WEAPONS


class Command(BaseCommand):
    help = "Enable and update unambiguous existing German Essential resources."

    def handle(self, **options):
        self._sync(Weapon, WEAPONS, ("damage", "range", "grip", "properties"))
        self._sync(RiotGear, ARMOR, ("protection", "load", "sealing", "properties"))

    def _sync(self, resource_model, definitions, fields):
        for definition in definitions:
            name, *values = definition
            matches = resource_model.objects.filter(name_de=name)
            if matches.count() != 1:
                self.stdout.write(
                    self.style.WARNING(
                        f"{resource_model.__name__}: {name}: {matches.count()} matches"
                    )
                )
                continue
            resource = matches.get()
            resource.essential_enabled = True
            for field, value in zip(fields, values):
                setattr(resource, f"essential_{field}", value)
            resource.save(
                update_fields=(
                    "essential_enabled",
                    *(f"essential_{field}" for field in fields),
                )
            )
            self.stdout.write(self.style.SUCCESS(f"{resource_model.__name__}: {name}"))
