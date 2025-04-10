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
)
from magic.models import SpellType, SpellVariant, SpellShape, SpellOrigin


class CreateItemForm(forms.Form):
    name = forms.CharField(label=_("Name"))
    description = forms.CharField(
        widget=forms.Textarea, label=_("Description"), required=False
    )
    type = forms.ModelChoiceField(
        queryset=ItemType.objects.all(), label=_("Category"), empty_label=None
    )
    weight = forms.DecimalField(label=_("Weight (kg)"))
    price = forms.DecimalField(label=_("Price"))
    concealment = forms.DecimalField(label=_("Concealment"))
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


class CreateRiotGearForm(forms.Form):
    name = forms.CharField(label=_("Name"))
    type = forms.ModelChoiceField(
        label=_("Type"), queryset=RiotGearType.objects.all(), required=True
    )
    description = forms.CharField(
        widget=forms.Textarea, label=_("Description"), required=False
    )
    encumbrance = forms.DecimalField(label=_("Encumbrance"))
    weight = forms.DecimalField(label=_("Weight (kg)"))
    price = forms.DecimalField(label=_("Price"))
    concealment = forms.DecimalField(label=_("Concealment"))
    add_to_character = forms.BooleanField(
        label=_("Add to character"), initial=True, required=False
    )


CreateRiotGearProtectionFormSet = forms.inlineformset_factory(
    parent_model=RiotGear,
    model=RiotGearProtection,
    fields=["protection_type", "value"],
    extra=3,
    can_delete=False,
    labels={"protection_type": _("Protection Type")},
)


class CreateWeaponForm(forms.Form):
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
    weight = forms.DecimalField(label=_("Weight (kg)"))
    price = forms.DecimalField(label=_("Price"))
    add_to_character = forms.BooleanField(
        label=_("Add to character"), initial=True, required=False
    )


CreateWeaponKeywordFormSet = forms.inlineformset_factory(
    parent_model=Weapon,
    model=WeaponKeyword,
    fields=["keyword", "value"],
    extra=3,
    can_delete=False,
    labels={"keyword": _("Keyword")},
)


class CreateBaseSpellForm(forms.Form):
    name = forms.CharField(label=_("Name"))
    rules = forms.CharField(widget=forms.Textarea, label=_("Rules"))
    spell_point_cost = forms.DecimalField(label=_("Spell Point Cost"))
    arcana_cost = forms.DecimalField(label=_("Arcana Cost"))
    range = forms.DecimalField(label=_("Range"))
    actions = forms.DecimalField(label=_("Actions"))
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
