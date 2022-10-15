from django import forms
from django.utils.translation import ugettext_lazy as _

from characters.models import Character
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
    lineage = forms.ModelChoiceField(queryset=Lineage.objects.all(), empty_label=None)
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


class CreateRandomNPCForm(CreateCharacterDataForm):
    starting_reputation = forms.IntegerField(
        label=_('Starting Reputation'),
        initial=50)
