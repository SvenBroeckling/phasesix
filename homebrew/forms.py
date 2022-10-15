from django import forms
from django.utils.translation import ugettext_lazy as _

from armory.models import ItemType, WeaponType
from magic.models import SpellType, SpellVariant, SpellShape


class CreateItemForm(forms.Form):
    name = forms.CharField(label=_('Name'))
    description = forms.CharField(widget=forms.Textarea, label=_('Description'), required=False)
    type = forms.ModelChoiceField(queryset=ItemType.objects.all(), label=_('Category'), empty_label=None)
    weight = forms.DecimalField(label=_('Weight (kg)'))
    price = forms.DecimalField(label=_('Price'))
    concealment = forms.DecimalField(label=_('Concealment'))
    charges = forms.DecimalField(
        label=_('Charges'),
        help_text=_('Leave blank for non-chargeable items'),
        required=False)
    add_to_character = forms.BooleanField(label=_('Add to character'), initial=True, required=False)


class CreateRiotGearForm(forms.Form):
    name = forms.CharField(label=_('Name'))
    description = forms.CharField(widget=forms.Textarea, label=_('Description'), required=False)
    protection = forms.DecimalField(label=_('Protection'))
    evasion = forms.DecimalField(label=_('Evasion'))
    weight = forms.DecimalField(label=_('Weight (kg)'))
    price = forms.DecimalField(label=_('Price'))
    concealment = forms.DecimalField(label=_('Concealment'))
    add_to_character = forms.BooleanField(label=_('Add to character'), initial=True, required=False)


class CreateWeaponForm(forms.Form):
    name = forms.CharField(label=_('Name'))
    description = forms.CharField(widget=forms.Textarea, label=_('Description'), required=False)
    type = forms.ModelChoiceField(queryset=WeaponType.objects.all(), label=_('Category'), empty_label=None)
    is_hand_to_hand_weapon = forms.BooleanField(label=_('Is hand to hand weapon'), required=False)
    bonus_dice = forms.DecimalField(label=_('Bonus Dice'))
    capacity = forms.DecimalField(label=_('Capacity'))
    wounds = forms.DecimalField(label=_('Bonus Wounds'))
    piercing = forms.DecimalField(label=_('Piercing'))
    concealment = forms.DecimalField(label=_('Concealment'))
    weight = forms.DecimalField(label=_('Weight (kg)'))
    price = forms.DecimalField(label=_('Price'))
    range_meter = forms.DecimalField(label=_('Range (meter)'))
    add_to_character = forms.BooleanField(label=_('Add to character'), initial=True, required=False)


class CreateBaseSpellForm(forms.Form):
    name = forms.CharField(label=_('Name'))
    rules = forms.CharField(widget=forms.Textarea, label=_('Rules'))
    spell_point_cost = forms.DecimalField(label=_('Spell Point Cost'))
    arcana_cost = forms.DecimalField(label=_('Arcana Cost'))
    power = forms.DecimalField(label=_('Power'))
    range = forms.DecimalField(label=_('Range'))
    actions = forms.DecimalField(label=_('Actions'))
    type = forms.ModelChoiceField(queryset=SpellType.objects.all(), label=_('School'), empty_label=None)
    variant = forms.ModelChoiceField(queryset=SpellVariant.objects.all(), label=_('Variant'), empty_label=None)
    shape = forms.ModelChoiceField(queryset=SpellShape.objects.all(), label=_('Shape'), required=False)
    is_ritual = forms.BooleanField(label=_('Is ritual'), required=False)
    add_to_character = forms.BooleanField(label=_('Add to character'), initial=True, required=False)
