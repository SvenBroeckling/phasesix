from django import forms
from django.utils.translation import ugettext_lazy as _

from armory.models import Weapon, RiotGear, WeaponModification

COVER_CHOICES = (
    (7, _('no cover')),
    (4, '4+'),
    (5, '5+'),
    (6, '6+'),
)


class CombatSimDummyForm(forms.Form):
    weapon = forms.ModelChoiceField(Weapon.objects.all(), label=_('Weapon'))
    riot_gear = forms.ModelChoiceField(RiotGear.objects.all(), label=_('Armor'), required=False)
    attack_value = forms.IntegerField(label=_('Attack value'))
    cover = forms.ChoiceField(label=_('Cover'), choices=COVER_CHOICES)
    health = forms.IntegerField(label=_('Health'))
