from django import forms
from django.utils.translation import gettext_lazy as _

from armory.models import CurrencyMap
from characters.models import Character
from pantheon.models import Entity
from rules.models import Lineage, Extension


class CharacterImageForm(forms.ModelForm):
    class Meta:
        model = Character
        fields = ('name', 'description', 'image', 'backdrop_image')


class CreateCharacterExtensionsForm(forms.Form):
    extensions = forms.ModelMultipleChoiceField(
        queryset=Extension.objects.filter(type__in=['x', 'w'], is_mandatory=False, is_active=True),
        label=_('Extensions'),
        required=False,
        widget=forms.SelectMultiple(attrs={'style': 'display: none'}))


class CreateCharacterDataForm(forms.Form):
    name = forms.CharField(label=_('Name'), max_length=80)
    lineage = forms.ModelChoiceField(
        queryset=Lineage.objects.all(),
        empty_label=None,
        label=_('Lineage'))
    currency_map = forms.ModelChoiceField(
        queryset=CurrencyMap.objects.all(),
        required=True,
        empty_label=None,
        label=_('Currency Map'))
    seed_money = forms.IntegerField(label=_('Seed Money'), min_value=0, max_value=100000, initial=2000)
    epoch = forms.ModelChoiceField(
        queryset=Extension.objects.filter(type='e', is_mandatory=False, is_active=True),
        label=_('Epoch'),
        widget=forms.HiddenInput())
    world = forms.ModelChoiceField(
        queryset=Extension.objects.filter(type='w', is_mandatory=False, is_active=True),
        label=_('Epoch'),
        widget=forms.HiddenInput())
    extensions = forms.ModelMultipleChoiceField(
        queryset=Extension.objects.filter(type__in=['x'], is_mandatory=False, is_active=True),
        label=_('Extensions'),
        required=False,
        widget=forms.SelectMultiple(attrs={'style': 'display: none'}))
    size = forms.IntegerField(label=_('Size'), required=False)
    weight = forms.IntegerField(label=_('Weight'), required=False)
    date_of_birth = forms.CharField(label=_('Date of birth'), required=False)
    entity = forms.ModelChoiceField(
        queryset=Entity.objects.all(),
        required=False,
        empty_label=_('None'),
        label=_('Entity'))
    attitude = forms.IntegerField(label=_('Attitude'), required=False)


class CreateRandomNPCForm(CreateCharacterDataForm):
    starting_reputation = forms.IntegerField(
        label=_('Starting Reputation'),
        initial=50)
