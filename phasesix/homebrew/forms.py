from django import forms
from django.utils.translation import gettext_lazy as _

from armory.models import (
    WeaponKeyword,
    Weapon,
    RiotGearProtection,
    RiotGear,
    Item,
    AttackMode,
)
from body_modifications.models import BodyModification, BodyModificationSocketLocation
from horror.models import Quirk, QuirkModifier
from magic.models import BaseSpell
from rules.models import Template, TemplateModifier
from worlds.models import Language


class CreateHomebrewForm(forms.ModelForm):
    formset_class = None

    add_to_character = forms.BooleanField(
        label=_("Add to character"), initial=True, required=False
    )

    def __init__(self, *args, **kwargs):
        self.character = kwargs.pop("character")
        self.campaign = kwargs.pop("campaign")
        self.request = kwargs.pop("request")
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.created_by = self.request.user
        obj.is_homebrew = True
        obj.homebrew_character = self.character
        obj.homebrew_campaign = self.campaign
        if commit:
            obj.save()
            self.save_m2m()
            if self.formset_class:
                formset = self.formset_class(self.request.POST, instance=obj)
                if formset.is_valid():
                    formset.save()
        return obj


class CreateItemForm(CreateHomebrewForm):
    class Meta:
        model = Item
        fields = [
            "name_de",
            "description_de",
            "rarity",
            "type",
            "weight",
            "price",
            "concealment",
            "charges",
            "is_container",
        ]
        help_texts = {
            "charges": _("Leave blank for non-chargeable items"),
            "is_container": _("Check if this item can hold other items"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["weight"].initial = 1
        self.fields["price"].initial = 10
        self.fields["concealment"].initial = 0

    def save(self, commit=True):
        item = super().save(commit=commit)
        if self.character is not None and self.cleaned_data["add_to_character"]:
            self.character.characteritem_set.create(item=item)
        return item


CreateRiotGearProtectionFormSet = forms.inlineformset_factory(
    parent_model=RiotGear,
    model=RiotGearProtection,
    fields=["protection_type", "value"],
    extra=3,
    can_delete=False,
    labels={"protection_type": _("Protection Type")},
)


class CreateRiotGearForm(CreateHomebrewForm):
    formset_class = CreateRiotGearProtectionFormSet

    class Meta:
        model = RiotGear
        fields = [
            "name_de",
            "type",
            "description_de",
            "encumbrance",
            "weight",
            "price",
            "concealment",
        ]

    def save(self, commit=True):
        riot_gear = super().save(commit=commit)
        if self.character is not None and self.cleaned_data["add_to_character"]:
            self.character.characterriotgear_set.create(riot_gear=riot_gear)
        return riot_gear


CreateWeaponKeywordFormSet = forms.inlineformset_factory(
    parent_model=Weapon,
    model=WeaponKeyword,
    fields=["keyword", "value"],
    extra=3,
    can_delete=False,
    labels={"keyword": _("Keyword")},
)


class CreateWeaponForm(CreateHomebrewForm):
    formset_class = CreateWeaponKeywordFormSet

    class Meta:
        model = Weapon
        fields = [
            "name_de",
            "description_de",
            "type",
            "is_hand_to_hand_weapon",
            "is_throwing_weapon",
            "weight",
            "price",
        ]

    def save(self, commit=True):
        weapon = super().save(commit=commit)
        if weapon.is_hand_to_hand_weapon:
            weapon.attack_modes.add(AttackMode.objects.get(name_en="Hand to Hand"))
        elif weapon.is_throwing_weapon:
            weapon.attack_modes.add(AttackMode.objects.get(name_en="Throwing"))
        else:
            weapon.attack_modes.add(AttackMode.objects.get(name_en="Burst mode"))
            weapon.attack_modes.add(AttackMode.objects.get(name_en="Single shot"))

        if self.character is not None and self.cleaned_data["add_to_character"]:
            self.character.characterweapon_set.create(weapon=weapon)

        return weapon


class CreateBaseSpellForm(CreateHomebrewForm):
    class Meta:
        model = BaseSpell
        fields = [
            "name_de",
            "rules_de",
            "spell_point_cost",
            "arcana_cost",
            "range",
            "actions",
            "origin",
            "type",
            "variant",
            "shape",
            "is_ritual",
        ]

    def save(self, commit=True):
        base_spell = super().save(commit=commit)
        if self.character is not None and self.cleaned_data["add_to_character"]:
            self.character.characterspell_set.create(spell=base_spell)
        return base_spell


CreateBodyModificationLocationFormSet = forms.inlineformset_factory(
    parent_model=BodyModification,
    model=BodyModificationSocketLocation,
    fields=["socket_location", "socket_amount"],
    extra=2,
    can_delete=False,
)


class CreateBodyModificationForm(CreateHomebrewForm):
    formset_class = CreateBodyModificationLocationFormSet

    class Meta:
        model = BodyModification
        fields = [
            "name_de",
            "type",
            "description_de",
            "rules_de",
            "price",
            "rarity",
            "bio_strain",
            "energy_consumption_ma",
            "charges",
        ]

    def save(self, commit=True):
        body_modification = super().save(commit=commit)
        if self.character is not None and self.cleaned_data["add_to_character"]:
            bl = body_modification.bodymodificationsocketlocation_set.first()
            self.character.characterbodymodification_set.create(
                body_modification=body_modification,
                socket_location=bl.socket_location,
                socket_amount=bl.socket_amount,
            )
        return body_modification


CreateTemplateModifierFormSet = forms.inlineformset_factory(
    parent_model=Template,
    model=TemplateModifier,
    fields=[
        "aspect",
        "aspect_modifier",
        "attribute",
        "attribute_modifier",
        "skill",
        "skill_modifier",
        "knowledge",
        "knowledge_modifier",
        "unlocks_spell_origin",
        "allows_priest_actions",
    ],
    extra=2,
    can_delete=False,
)


class CreateTemplateForm(CreateHomebrewForm):
    formset_class = CreateTemplateModifierFormSet

    class Meta:
        model = Template
        fields = [
            "name_de",
            "category",
            "rules_de",
            "cost",
            "show_rules_in_combat",
            "show_in_attack_dice_rolls",
            "quote",
            "quote_author",
        ]

    def save(self, commit=True):
        template = super().save(commit=commit)
        if self.character is not None and self.cleaned_data["add_to_character"]:
            self.character.charactertemplate_set.create(template=template)
        return template


CreateQuirkModifierFormSet = forms.inlineformset_factory(
    parent_model=Quirk,
    model=QuirkModifier,
    fields=[
        "aspect",
        "aspect_modifier",
        "attribute",
        "attribute_modifier",
        "skill",
        "skill_modifier",
        "knowledge",
        "knowledge_modifier",
        "unlocks_spell_origin",
        "allows_priest_actions",
    ],
    extra=2,
    can_delete=False,
)


class CreateQuirkForm(CreateHomebrewForm):
    formset_class = CreateQuirkModifierFormSet

    class Meta:
        model = Quirk
        fields = [
            "name_de",
            "category",
            "rules_de",
            "description_de",
        ]

    def save(self, commit=True):
        quirk = super().save(commit=commit)
        if self.character is not None and self.cleaned_data["add_to_character"]:
            self.character.quirks.add(quirk)
        return quirk


class CreateLanguageForm(CreateHomebrewForm):
    class Meta:
        model = Language
        fields = [
            "name_de",
            "country_name_de",
            "amount_of_people_speaking",
            "group",
        ]

    def save(self, commit=True):
        language = super().save(commit=commit)
        if self.character is not None and self.cleaned_data["add_to_character"]:
            self.character.characterlanguage_set.create(language=language)
        return language
