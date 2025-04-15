from abc import abstractmethod

from django.utils.translation import get_language

from armory.models import Weapon, WeaponType, ItemType, Item, RiotGearType, RiotGear
from body_modifications.models import (
    BodyModificationType,
    BodyModification,
    SocketLocation,
    BodyModificationSocketLocation,
)
from characters.templatetags.characters_extras import for_extensions
from homebrew.forms import (
    CreateWeaponKeywordFormSet,
    CreateWeaponForm,
    CreateItemForm,
    CreateRiotGearForm,
    CreateRiotGearProtectionFormSet,
    CreateBaseSpellForm,
    CreateBodyModificationForm,
    CreateBodyModificationLocationFormSet,
    CreateTemplateForm,
    CreateTemplateModifierFormSet,
    CreateQuirkForm,
    CreateQuirkModifierFormSet,
    CreateLanguageForm,
)
from horror.models import QuirkCategory, Quirk
from magic.models import SpellOrigin, BaseSpell
from rules.models import TemplateCategory, Template, Extension
from worlds.models import LanguageGroup, Language


def get_character_object_class(object_type):
    return filter(
        lambda x: x.object_type == object_type, CharacterObject.__subclasses__()
    ).__next__()


class CharacterObject:
    model = None
    child_model = None
    object_type = None
    homebrew_form_class = None
    homebrew_formset_class = None

    def __init__(self, request, character, campaign=None):
        self.character = character
        self.campaign = campaign
        self.request = request

    @property
    def character_or_campaign(self):
        return self.character or self.campaign

    def get_category_qs(self):
        try:
            qs = self.model.objects.for_extensions(
                self.character_or_campaign.extensions
            )
        except AttributeError:  # model without extensions
            qs = self.model.objects.all()

        return qs.filter(
            id__in=[
                category.id
                for category in qs
                if for_extensions(
                    category.child_item_qs(), self.get_extension_qs()
                ).exists()
            ]
        ).distinct()

    def get_homebrew_qs(self):
        return self.child_model.objects.homebrew(
            character=self.character, campaign=self.campaign
        )

    def get_extension_qs(self):
        if not self.character_or_campaign.extensions.exists():
            if (
                self.request.world_configuration
                and self.request.world_configuration.world
            ):
                return Extension.objects.for_world(
                    self.request.world_configuration.world
                )
            return Extension.objects.all()
        return self.character_or_campaign.extensions.all()

    @abstractmethod
    def remove(self, pk):
        raise NotImplementedError("Remove method not implemented")

    @abstractmethod
    def add(self, pk):
        raise NotImplementedError("Add method not implemented")

    @property
    def homebrew_form(self):
        if not self.homebrew_form_class:
            return None
        return self.homebrew_form_class(
            character=self.character,
            campaign=self.campaign,
            request=self.request,
        )

    @property
    def homebrew_formset(self):
        if not self.homebrew_formset_class:
            return None
        return self.homebrew_formset_class()


class WeaponObject(CharacterObject):
    object_type = "weapon"
    model = WeaponType
    child_model = Weapon
    homebrew_form_class = CreateWeaponForm
    homebrew_formset_class = CreateWeaponKeywordFormSet

    def remove(self, pk):
        self.character.characterweapon_set.filter(id=pk).delete()

    def add(self, pk):
        obj = Weapon.objects.get(id=pk)
        self.character.characterweapon_set.create(weapon=obj)


class ItemObject(CharacterObject):
    object_type = "item"
    model = ItemType
    child_model = Item
    homebrew_form_class = CreateItemForm
    homebrew_formset_class = None

    def remove(self, pk):
        item = Item.objects.get(id=pk)
        if self.character.characteritem_set.filter(item=item).exists():
            ci = self.character.characteritem_set.filter(item=item).latest("id")
            if ci.quantity > 1:
                ci.quantity -= 1
                ci.save()
            else:
                ci.delete()

    def add(self, pk):
        item = Item.objects.get(id=pk)
        if (
            self.character.characteritem_set.filter(item=item).exists()
            and not item.is_container
        ):
            ci = self.character.characteritem_set.filter(item=item).latest("id")
            ci.quantity += 1
            ci.save()
        else:
            self.character.characteritem_set.create(item=item)


class RiotGearObject(CharacterObject):
    object_type = "riot_gear"
    model = RiotGearType
    child_model = RiotGear
    homebrew_form_class = CreateRiotGearForm
    homebrew_formset_class = CreateRiotGearProtectionFormSet

    def remove(self, pk):
        self.character.characterriotgear_set.filter(id=pk).delete()

    def add(self, pk):
        obj = RiotGear.objects.get(id=pk)
        self.character.characterriotgear_set.create(riot_gear=obj)


class SpellObject(CharacterObject):
    object_type = "spell"
    model = SpellOrigin
    child_model = BaseSpell
    homebrew_form_class = CreateBaseSpellForm
    homebrew_formset_class = None

    def get_category_qs(self):
        if self.character:
            return self.character.unlocked_spell_origins
        return SpellOrigin.objects.all()

    def remove(self, pk):
        self.character.characterspell_set.filter(id=pk).delete()

    def add(self, pk):
        obj = BaseSpell.objects.get(id=pk)
        self.character.characterspell_set.create(spell=obj)


class TemplateObject(CharacterObject):
    object_type = "template"
    model = TemplateCategory
    child_model = Template
    homebrew_form_class = CreateTemplateForm
    homebrew_formset_class = CreateTemplateModifierFormSet

    def get_category_qs(self):
        return super().get_category_qs().filter(allow_for_reputation=True)

    def remove(self, pk):
        self.character.charactertemplate_set.filter(id=pk).delete()

    def add(self, pk):
        template = Template.objects.get(id=pk)
        if template.cost <= self.character.reputation_available:
            self.character.add_template(template)
        else:
            raise ValueError()


class QuirkObject(CharacterObject):
    object_type = "quirk"
    model = QuirkCategory
    child_model = Quirk
    homebrew_form_class = CreateQuirkForm
    homebrew_formset_class = CreateQuirkModifierFormSet

    def remove(self, pk):
        self.character.quirks.remove(pk)

    def add(self, pk):
        obj = Quirk.objects.get(id=pk)
        self.character.quirks.add(obj)


class LanguageObject(CharacterObject):
    object_type = "language"
    model = LanguageGroup
    child_model = Language
    homebrew_form_class = CreateLanguageForm
    homebrew_formset_class = None

    def get_category_qs(self):
        """The world extension overides the epoch extensions, if present."""
        qs = super().get_category_qs()
        world_extension = self.character_or_campaign.extensions.filter(type="w").first()
        if world_extension and world_extension.exclusive_languages:
            qs = qs.filter(language__extensions__type="w")
        return qs.order_by(f"name_{get_language()}")

    def remove(self, pk):
        self.character.characterlanguage_set.filter(id=pk).delete()

    def add(self, pk):
        language = Language.objects.get(id=pk)
        self.character.characterlanguage_set.get_or_create(language=language)


class BodyModificationObject(CharacterObject):
    object_type = "body_modification"
    model = BodyModificationType
    child_model = BodyModification
    homebrew_form_class = CreateBodyModificationForm
    homebrew_formset_class = CreateBodyModificationLocationFormSet

    def remove(self, pk):
        self.character.characterbodymodification_set.filter(id=pk).delete()

    def add(self, pk):
        obj = BodyModification.objects.get(id=pk)
        socket_location = SocketLocation.objects.get(
            id=self.request.POST.get("socket_location_pk")
        )
        bm_socket_location = BodyModificationSocketLocation.objects.get(
            body_modification=obj, socket_location=socket_location
        )

        self.character.characterbodymodification_set.create(
            body_modification=obj,
            socket_location=socket_location,
            socket_amount=bm_socket_location.socket_amount,
        )
