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
from magic.models import BaseSpell


class CreateHomebrewForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        self.character = kwargs.pop("character")
        self.campaign = kwargs.pop("campaign")
        self.request = kwargs.pop("request")
        super().__init__(*args, **kwargs)


class CreateItemForm(CreateHomebrewForm):
    add_to_character = forms.BooleanField(
        label=_("Add to character"), initial=True, required=False
    )

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
        item = super().save(commit=False)
        item.created_by = self.request.user
        item.is_homebrew = True
        item.homebrew_character = self.character
        item.homebrew_campaign = self.campaign

        if commit:
            item.save()
        if self.character is not None and self.cleaned_data["add_to_character"]:
            self.character.characteritem_set.create(item=item)

        return item


class CreateRiotGearForm(CreateHomebrewForm):
    add_to_character = forms.BooleanField(
        label=_("Add to character"), initial=True, required=False
    )

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
        riot_gear = super().save(commit=False)
        riot_gear.created_by = self.request.user
        riot_gear.is_homebrew = True
        riot_gear.homebrew_character = self.character
        riot_gear.homebrew_campaign = self.campaign

        if commit:
            riot_gear.save()
        formset = CreateRiotGearProtectionFormSet(self.request.POST, instance=riot_gear)
        for formset_form in formset:
            if formset_form.is_valid():
                try:
                    protection_type = formset_form.cleaned_data["protection_type"]
                    value = formset_form.cleaned_data["value"]
                    riot_gear.riotgearprotection_set.create(
                        protection_type=protection_type, value=value
                    )
                except KeyError:  # Empty form
                    pass

        if self.character is not None and self.cleaned_data["add_to_character"]:
            self.character.characterriotgear_set.create(riot_gear=riot_gear)

        return riot_gear


CreateRiotGearProtectionFormSet = forms.inlineformset_factory(
    parent_model=RiotGear,
    model=RiotGearProtection,
    fields=["protection_type", "value"],
    extra=3,
    can_delete=False,
    labels={"protection_type": _("Protection Type")},
)


class CreateWeaponForm(CreateHomebrewForm):
    add_to_character = forms.BooleanField(
        label=_("Add to character"), initial=True, required=False
    )

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
        weapon = super().save(commit=False)
        weapon.created_by = self.request.user
        weapon.is_homebrew = True
        weapon.homebrew_character = self.character
        weapon.homebrew_campaign = self.campaign

        if commit:
            weapon.save()
        if weapon.is_hand_to_hand_weapon:
            weapon.attack_modes.add(AttackMode.objects.get(name_en="Hand to Hand"))
        elif weapon.is_throwing_weapon:
            weapon.attack_modes.add(AttackMode.objects.get(name_en="Throwing"))
        else:
            weapon.attack_modes.add(AttackMode.objects.get(name_en="Burst mode"))
            weapon.attack_modes.add(AttackMode.objects.get(name_en="Single shot"))

        formset = CreateWeaponKeywordFormSet(self.request.POST, instance=weapon)
        for formset_form in formset:
            if formset_form.is_valid():
                try:
                    keyword = formset_form.cleaned_data["keyword"]
                    value = formset_form.cleaned_data["value"]
                    weapon.weaponkeyword_set.create(keyword=keyword, value=value)
                except KeyError:  # Empty form
                    pass

        if self.character is not None and self.cleaned_data["add_to_character"]:
            self.character.characterweapon_set.create(weapon=weapon)

        return weapon


CreateWeaponKeywordFormSet = forms.inlineformset_factory(
    parent_model=Weapon,
    model=WeaponKeyword,
    fields=["keyword", "value"],
    extra=3,
    can_delete=False,
    labels={"keyword": _("Keyword")},
)


class CreateBaseSpellForm(CreateHomebrewForm):
    add_to_character = forms.BooleanField(
        label=_("Add to character"), initial=True, required=False
    )

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
        base_spell = super().save(commit=False)
        base_spell.created_by = self.request.user
        base_spell.is_homebrew = True
        base_spell.homebrew_character = self.character
        base_spell.homebrew_campaign = self.campaign

        if commit:
            base_spell.save()
        if self.character is not None and self.cleaned_data["add_to_character"]:
            self.character.characterspell_set.create(spell=base_spell)

        return base_spell


class CreateBodyModificationForm(CreateHomebrewForm):
    add_to_character = forms.BooleanField(
        label=_("Add to character"), initial=True, required=False
    )

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
        body_modification = super().save(commit=False)
        body_modification.created_by = self.request.user
        body_modification.is_homebrew = True
        body_modification.homebrew_character = self.character
        body_modification.homebrew_campaign = self.campaign

        if commit:
            body_modification.save()
        formset = CreateBodyModificationLocationFormSet(
            self.request.POST, instance=body_modification
        )
        for formset_form in formset:
            if formset_form.is_valid():
                try:
                    location = formset_form.cleaned_data["socket_location"]
                    amount = formset_form.cleaned_data["socket_amount"]
                    body_modification.bodymodificationsocketlocation_set.create(
                        socket_location=location, socket_amount=amount
                    )
                except KeyError:  # Empty form
                    pass
                else:
                    if (
                        self.character is not None
                        and self.cleaned_data["add_to_character"]
                    ):
                        self.character.characterbodymodification_set.create(
                            body_modification=body_modification,
                            socket_location=location,
                            socket_amount=amount,
                        )

        return body_modification


CreateBodyModificationLocationFormSet = forms.inlineformset_factory(
    parent_model=BodyModification,
    model=BodyModificationSocketLocation,
    fields=["socket_location", "socket_amount"],
    extra=1,
    can_delete=False,
)
