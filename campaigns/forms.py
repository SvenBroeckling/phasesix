from django import forms
from django.utils.translation import ugettext_lazy as _

from campaigns.models import Scene, Campaign
from rules.models import Extension


class CreateCampaignExtensionsForm(forms.Form):
    extensions = forms.ModelMultipleChoiceField(
        queryset=Extension.objects.filter(type__in=['x', 'w'], is_mandatory=False, is_active=True),
        label=_('Extensions'),
        required=False,
        widget=forms.SelectMultiple(attrs={'style': 'display: none'}))


class SettingsForm(forms.ModelForm):
    class Meta:
        model = Campaign
        fields = 'name', 'abstract', 'epoch', 'extensions', 'currency_map', 'character_visibility', 'discord_webhook_url', 'image', 'backdrop_image'


class SceneForm(forms.ModelForm):
    class Meta:
        model = Scene
        fields = ('name', 'text')
