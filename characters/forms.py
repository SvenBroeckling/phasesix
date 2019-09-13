from django import forms
from django.utils.translation import ugettext_lazy as _

from characters.models import Character
from rules.models import Lineage, Extension


class CharacterImageForm(forms.ModelForm):
    class Meta:
        model = Character
        fields = ('name', 'description', 'image', 'backdrop_image')


class CreateCharacterForm(forms.Form):
    name = forms.CharField(label=_('Name'), max_length=80)
    lineage = forms.ModelChoiceField(queryset=Lineage.objects.all())
    epoch = forms.ModelChoiceField(
        queryset=Extension.objects.filter(is_epoch=True, is_mandatory=False),
        label=_('Epoch'))
    extensions = forms.ModelMultipleChoiceField(
        queryset=Extension.objects.filter(is_epoch=False, is_mandatory=False),
        label=_('Extensions'),
        required=False)
