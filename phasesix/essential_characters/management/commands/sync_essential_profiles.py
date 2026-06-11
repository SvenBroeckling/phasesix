from django.core.management.base import BaseCommand
from armory.models import Weapon, RiotGear
from essential_characters.models import EssentialArmorProfile, EssentialWeaponProfile

WEAPONS = [
    ("Unbewaffnet", "1", "Nahkampf", "10", "Nichttödlich"),
    ("Messer", "1", "Nahkampf", "10", "Verbergbar"),
    ("Dolch", "1", "Nahkampf/nah", "10", "Verbergbar, Wurf"),
    ("Knüppel", "1", "Nahkampf", "0", "Brutal"),
    ("Stab", "1", "Nahkampf/nah", "0", "Abfangen"),
    ("Beil", "2", "Nahkampf/nah", "0", "Wurf"),
    ("Schwert", "2", "Nahkampf", "10", "Ausgewogen"),
    ("Streitkolben", "2", "Nahkampf", "0", "Wuchtig"),
    ("Speer", "2", "Nahkampf/nah", "0", "Abfangen, Aufsetzen"),
    ("Zweihandaxt", "3", "Nahkampf", "-10", "Schwer, Laut"),
    ("Bogen", "2", "nah/fern", "0", "Zweihändig, Nachladen 1"),
    ("Armbrust", "3", "nah/fern", "-10", "Zweihändig, Nachladen 2"),
    ("Schleuder", "1", "nah/fern", "0", "Nachladen 1"),
]
ARMOR = [
    ("Gepolsterter Mantel", "1", "0", "0", "Verbergbar"),
    ("Geschichtete Roben", "1", "0", "1", "Ritual"),
    ("Lederwams", "1", "0", "0", "Feldtauglich"),
    ("Flickwerk-Kettenhemd", "2", "1", "0", "-"),
    ("Brigantine", "2", "1", "1", "Verstärkt"),
    ("Halbe Platte", "3", "2", "1", "Schwer"),
    ("Vollharnisch", "3", "2", "2", "Kriegsgerät"),
]


class Command(BaseCommand):
    help = "Create or update Essential profiles for unambiguous existing German resources."

    def handle(self, **options):
        self._sync(Weapon, EssentialWeaponProfile, WEAPONS, "weapon", ("damage", "range", "grip", "properties"))
        self._sync(RiotGear, EssentialArmorProfile, ARMOR, "riot_gear", ("protection", "load", "sealing", "properties"))

    def _sync(self, resource_model, profile_model, definitions, relation, fields):
        for definition in definitions:
            name, *values = definition
            matches = resource_model.objects.filter(name_de=name)
            if matches.count() != 1:
                self.stdout.write(self.style.WARNING(f"{resource_model.__name__}: {name}: {matches.count()} matches"))
                continue
            defaults = dict(zip(fields, values))
            profile_model.objects.update_or_create(**{relation: matches.get()}, defaults=defaults)
            self.stdout.write(self.style.SUCCESS(f"{resource_model.__name__}: {name}"))
