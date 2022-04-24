from django import forms
from django.utils.translation import ugettext_lazy as _

from armory.models import ItemType, WeaponType


class CreateItemForm(forms.Form):
    name = forms.CharField(label=_('Name'))
    description = forms.CharField(widget=forms.Textarea, label=_('Description'))
    type = forms.ModelChoiceField(queryset=ItemType.objects.all(), label=_('Category'), empty_label=None)
    weight = forms.DecimalField(label=_('Weight (kg)'))
    price = forms.DecimalField(label=_('Price'))
    concealment = forms.DecimalField(label=_('Concealment'))
    add_to_character = forms.BooleanField(label=_('Add to character'), initial=True)


class CreateRiotGearForm(forms.Form):
    name = forms.CharField(label=_('Name'))
    description = forms.CharField(widget=forms.Textarea, label=_('Description'))
    protection = forms.DecimalField(label=_('Protection'))
    evasion = forms.DecimalField(label=_('Evasion'))
    weight = forms.DecimalField(label=_('Weight (kg)'))
    price = forms.DecimalField(label=_('Price'))
    concealment = forms.DecimalField(label=_('Concealment'))
    add_to_character = forms.BooleanField(label=_('Add to character'), initial=True)


class CreateWeaponForm(forms.Form):
    name = forms.CharField(label=_('Name'))
    description = forms.CharField(widget=forms.Textarea, label=_('Description'))
    type = forms.ModelChoiceField(queryset=WeaponType.objects.all(), label=_('Category'), empty_label=None)
    is_hand_to_hand_weapon = forms.BooleanField(label=_('Is hand to hand weapon'))
    bonus_dice = forms.DecimalField(label=_('Bonus Dice'))
    capacity = forms.DecimalField(label=_('Capacity'))
    wounds = forms.DecimalField(label=_('Bonus Wounds'))
    piercing = forms.DecimalField(label=_('Piercing'))
    concealment = forms.DecimalField(label=_('Concealment'))
    weight = forms.DecimalField(label=_('Weight (kg)'))
    price = forms.DecimalField(label=_('Price'))
    range_meter = forms.DecimalField(label=_('Range (meter)'))
    add_to_character = forms.BooleanField(label=_('Add to character'), initial=True)
