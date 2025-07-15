from django.utils.translation import gettext_lazy as _

from armory.models import Weapon, RiotGear, WeaponModification, Item
from body_modifications.models import BodyModification
from characters.models import CharacterTemplate
from horror.models import Quirk
from magic.models import BaseSpell, SpellTemplate
from rulebook.models import Chapter
from rules.models import Template as CharacterTemplate, Foe
from worlds.models import WikiPage


def get_appendix_class(name):
    for sc in Appendix.__subclasses__():
        if sc.name == name:
            return sc
    return None


class Appendix:
    name = ""
    title = ""
    chapter_id = ""

    def __init__(self, world_book):
        self.world_book = world_book

    @property
    def included_in_world_book(self):
        return self.get_linked_chapter() in self.world_book.chapters

    def get_linked_chapter(self):
        return Chapter.objects.get(identifier=self.chapter_id)

    def get_queryset(self):
        pass


class TemplatesAppendix(Appendix):
    name = "templates"
    title = _("Character Templates")
    chapter_id = "chapter-create"

    def get_queryset(self):
        return CharacterTemplate.objects.for_world(self.world_book.world).order_by(
            "category"
        )


class WeaponsAppendix(Appendix):
    name = "weapons"
    title = _("Weapons")
    chapter_id = "chapter-gear"

    def get_queryset(self):
        return Weapon.objects.for_world(self.world_book.world).order_by("type")


class WeaponModificationsAppendix(Appendix):
    name = "weapon_modifications"
    title = _("Weapon Modifications")
    chapter_id = "chapter-gear"

    def get_queryset(self):
        return WeaponModification.objects.for_world(self.world_book.world).order_by(
            "type"
        )


class RiotGearAppendix(Appendix):
    name = "riot_gear"
    title = _("Armor")
    chapter_id = "chapter-gear"

    def get_queryset(self):
        return RiotGear.objects.for_world(self.world_book.world).order_by("type")


class ItemsAppendix(Appendix):
    name = "items"
    title = _("Items")
    chapter_id = "chapter-gear"

    def get_queryset(self):
        return Item.objects.for_world(self.world_book.world).order_by("type")


class SpellsAppendix(Appendix):
    name = "spells"
    title = _("Spells")
    chapter_id = "chapter-magic"

    def get_queryset(self):
        return BaseSpell.objects.order_by("origin")


class SpellTemplatesAppendix(Appendix):
    name = "spell_templates"
    title = _("Spell Templates")
    chapter_id = "chapter-magic"

    def get_queryset(self):
        return SpellTemplate.objects.order_by("category")


class QuirksAppendix(Appendix):
    name = "quirks"
    title = _("Quirks")
    chapter_id = "chapter-horror"

    def get_queryset(self):
        return Quirk.objects.all()


class BodyModificationsAppendix(Appendix):
    name = "body_modifications"
    title = _("Body Modifications")
    chapter_id = "chapter-body_modifications"

    def get_queryset(self):
        return BodyModification.objects.all()


class FoesAppendix(Appendix):
    name = "foes"
    title = _("Foes")
    chapter_id = "chapter-combat"

    def get_queryset(self):
        return Foe.objects.for_extensions(self.world_book.world.extension).order_by(
            "type"
        )
