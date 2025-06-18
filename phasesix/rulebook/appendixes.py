from django.utils.translation import gettext_lazy as _

from armory.models import Weapon, RiotGear, WeaponModification
from body_modifications.models import BodyModification
from characters.models import CharacterTemplate
from horror.models import Quirk
from magic.models import BaseSpell, SpellTemplate
from rulebook.models import Chapter
from rules.models import Template as CharacterTemplate
from worlds.models import WikiPage


def get_appendix_class(name):
    for sc in Appendix.__subclasses__():
        if sc.name == name:
            return sc
    return None


class Appendix:
    name = ""
    title = ""

    def __init__(self, world_book):
        self.world_book = world_book

    def get_queryset(self):
        pass

    def get_image(self):
        return None


class TemplatesAppendix(Appendix):
    name = "templates"
    title = _("Character Templates")

    def get_queryset(self):
        return CharacterTemplate.objects.for_world(self.world_book.world).order_by(
            "category")

    def get_image(self):
        return Chapter.objects.get(identifier="chapter-create-a-character").image


class WeaponsAppendix(Appendix):
    name = "weapons"
    title = _("Weapons")

    def get_queryset(self):
        return Weapon.objects.for_world(self.world_book.world).order_by("type")

    def get_image(self):
        return Chapter.objects.get(identifier="chapter-gear").image


class WeaponModificationsAppendix(Appendix):
    name = "weapon_modifications"
    title = _("Weapon Modifications")

    def get_queryset(self):
        return WeaponModification.objects.for_world(self.world_book.world).order_by(
            "type")

    def get_image(self):
        return Chapter.objects.get(identifier="chapter-gear").image


class RiotGearAppendix(Appendix):
    name = "riot_gear"
    title = _("Armor")

    def get_queryset(self):
        return RiotGear.objects.for_world(self.world_book.world).order_by("type")

    def get_image(self):
        return Chapter.objects.get(identifier="chapter-gear").image


class SpellsAppendix(Appendix):
    name = "spells"
    title = _("Spells")

    def get_queryset(self):
        return BaseSpell.objects.order_by("origin")

    def get_image(self):
        return Chapter.objects.get(identifier="chapter-magic").image


class SpellTemplatesAppendix(Appendix):
    name = "spell_templates"
    title = _("Spell Templates")

    def get_queryset(self):
        return SpellTemplate.objects.order_by("category")

    def get_image(self):
        return Chapter.objects.get(identifier="chapter-magic").image


class QuirksAppendix(Appendix):
    name = "quirks"
    title = _("Quirks")

    def get_queryset(self):
        return Quirk.objects.all()

    def get_image(self):
        return Chapter.objects.get(identifier="chapter-horror").image


class BodyModificationsAppendix(Appendix):
    name = "body_modifications"
    title = _("Body Modifications")

    def get_queryset(self):
        return BodyModification.objects.all()

    def get_image(self):
        return Chapter.objects.get(identifier="chapter-body_modifications").image


class FoesAppendix(Appendix):
    name = "foes"
    title = _("Foes")

    def get_queryset(self):
        return WikiPage.objects.with_game_values().exclude(
            exclude_from_foe_search=True).for_world(
            self.world_book.world).order_by("parent")

    def get_image(self):
        return Chapter.objects.get(identifier="chapter-horror").image
