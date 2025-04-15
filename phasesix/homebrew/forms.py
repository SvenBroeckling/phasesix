from django import forms
from django.utils.translation import gettext_lazy as _

from armory.models import (
    ItemType,
    WeaponType,
    RiotGearType,
    WeaponKeyword,
    Weapon,
    RiotGearProtection,
    RiotGear,
    Item,
    AttackMode,
)
from magic.models import SpellType, SpellVariant, SpellShape, SpellOrigin, BaseSpell


class CreateHomebrewForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.character = kwargs.pop("character")
        self.campaign = kwargs.pop("campaign")
        self.request = kwargs.pop("request")
        super().__init__(*args, **kwargs)


class CreateItemForm(CreateHomebrewForm):
    name = forms.CharField(label=_("Name"))
    description = forms.CharField(
        widget=forms.Textarea, label=_("Description"), required=False
    )
    type = forms.ModelChoiceField(
        queryset=ItemType.objects.all(), label=_("Category"), empty_label=None
    )
    weight = forms.DecimalField(label=_("Weight (kg)"), initial=1)
    price = forms.DecimalField(label=_("Price"), initial=10)
    concealment = forms.DecimalField(label=_("Concealment"), initial=0)
    charges = forms.DecimalField(
        label=_("Charges"),
        help_text=_("Leave blank for non-chargeable items"),
        required=False,
    )
    is_container = forms.BooleanField(
        label=_("Is Container"),
        help_text=_("Check if this item can hold other items"),
        required=False,
    )
    add_to_character = forms.BooleanField(
        label=_("Add to character"), initial=True, required=False
    )

    def save(self):
        item = Item.objects.create(
            {
                "name_de": self.cleaned_data["name"],
                "description_de": self.cleaned_data["description"],
                "type": self.cleaned_data["type"],
                "weight": self.cleaned_data["weight"],
                "price": self.cleaned_data["price"],
                "concealment": self.cleaned_data["concealment"],
                "charges": self.cleaned_data["charges"],
                "is_container": self.cleaned_data["is_container"],
                "created_by": self.request.user,
                "is_homebrew": True,
                "homebrew_character": self.character,
                "homebrew_campaign": self.campaign,
            }
        )

        if self.character is not None and self.cleaned_data["add_to_character"]:
            self.character.characteritem_set.create(item=item)

        return item


class CreateRiotGearForm(CreateHomebrewForm):
    name = forms.CharField(label=_("Name"))
    type = forms.ModelChoiceField(
        label=_("Type"), queryset=RiotGearType.objects.all(), required=True, initial=1
    )
    description = forms.CharField(
        widget=forms.Textarea, label=_("Description"), required=False
    )
    encumbrance = forms.DecimalField(label=_("Encumbrance"), initial=1)
    weight = forms.DecimalField(label=_("Weight (kg)"), initial=1)
    price = forms.DecimalField(label=_("Price"), initial=100)
    concealment = forms.DecimalField(label=_("Concealment"), initial=0)
    add_to_character = forms.BooleanField(
        label=_("Add to character"), initial=True, required=False
    )

    def save(self):
        riot_gear = RiotGear.objects.create(
            type=self.cleaned_data["type"],
            name_de=self.cleaned_data["name"],
            description_de=self.cleaned_data["description"],
            encumbrance=self.cleaned_data["encumbrance"],
            weight=self.cleaned_data["weight"],
            price=self.cleaned_data["price"],
            concealment=self.cleaned_data["concealment"],
            created_by=self.request.user,
            is_homebrew=True,
            homebrew_character=self.character,
            homebrew_campaign=self.campaign,
        )
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


CreateRiotGearProtectionFormSet = forms.inlineformset_factory(
    parent_model=RiotGear,
    model=RiotGearProtection,
    fields=["protection_type", "value"],
    extra=3,
    can_delete=False,
    labels={"protection_type": _("Protection Type")},
)


class CreateWeaponForm(CreateHomebrewForm):
    name = forms.CharField(label=_("Name"))
    description = forms.CharField(
        widget=forms.Textarea, label=_("Description"), required=False
    )
    type = forms.ModelChoiceField(
        queryset=WeaponType.objects.all(), label=_("Category"), empty_label=None
    )
    is_hand_to_hand_weapon = forms.BooleanField(
        label=_("Is hand to hand weapon"), required=False
    )
    is_throwing_weapon = forms.BooleanField(
        label=_("Is throwing weapon"), required=False
    )
    weight = forms.DecimalField(label=_("Weight (kg)"), initial=1)
    price = forms.DecimalField(label=_("Price"), initial=100)
    add_to_character = forms.BooleanField(
        label=_("Add to character"), initial=True, required=False
    )

    def save(self):
        weapon = Weapon.objects.create(
            name_de=self.cleaned_data["name"],
            description_de=self.cleaned_data["description"],
            type=self.cleaned_data["type"],
            is_hand_to_hand_weapon=self.cleaned_data["is_hand_to_hand_weapon"],
            is_throwing_weapon=self.cleaned_data["is_throwing_weapon"],
            weight=self.cleaned_data["weight"],
            price=self.cleaned_data["price"],
            created_by=self.request.user,
            is_homebrew=True,
            homebrew_character=self.character,
            homebrew_campaign=self.campaign,
        )
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


CreateWeaponKeywordFormSet = forms.inlineformset_factory(
    parent_model=Weapon,
    model=WeaponKeyword,
    fields=["keyword", "value"],
    extra=3,
    can_delete=False,
    labels={"keyword": _("Keyword")},
)


class CreateBaseSpellForm(CreateHomebrewForm):
    name = forms.CharField(label=_("Name"))
    rules = forms.CharField(widget=forms.Textarea, label=_("Rules"))
    spell_point_cost = forms.DecimalField(label=_("Spell Point Cost"), initial=5)
    arcana_cost = forms.DecimalField(label=_("Arcana Cost"), initial=1)
    range = forms.DecimalField(label=_("Range"), initial=10)
    actions = forms.DecimalField(label=_("Actions"), initial=1)
    origin = forms.ModelChoiceField(
        queryset=SpellOrigin.objects.all(), label=_("Origin"), empty_label=None
    )
    type = forms.ModelChoiceField(
        queryset=SpellType.objects.all(), label=_("Type"), empty_label=None
    )
    variant = forms.ModelChoiceField(
        queryset=SpellVariant.objects.all(), label=_("Variant"), empty_label=None
    )
    shape = forms.ModelChoiceField(
        queryset=SpellShape.objects.all(), label=_("Shape"), required=False
    )
    is_ritual = forms.BooleanField(label=_("Is ritual"), required=False)
    add_to_character = forms.BooleanField(
        label=_("Add to character"), initial=True, required=False
    )

    def save(self):
        base_spell = BaseSpell.objects.create(
            name_de=self.cleaned_data["name"],
            rules_de=self.cleaned_data["rules"],
            spell_point_cost=self.cleaned_data["spell_point_cost"],
            arcana_cost=self.cleaned_data["arcana_cost"],
            range=self.cleaned_data["range"],
            actions=self.cleaned_data["actions"],
            origin=self.cleaned_data["origin"],
            type=self.cleaned_data["type"],
            variant=self.cleaned_data["variant"],
            shape=self.cleaned_data["shape"],
            is_ritual=self.cleaned_data["is_ritual"],
            created_by=self.request.user,
            is_homebrew=True,
            homebrew_character=self.character,
            homebrew_campaign=self.campaign,
        )
        if self.character is not None and self.cleaned_data["add_to_character"]:
            self.character.characterspell_set.create(spell=base_spell)
