from django import forms

from campaigns.models import Scene, Campaign


class SettingsForm(forms.ModelForm):
    class Meta:
        model = Campaign
        fields = 'name', 'abstract', 'epoch', 'extensions', 'currency_map', 'character_visibility', 'discord_webhook_url', 'image', 'backdrop_image'


class SceneForm(forms.ModelForm):
    class Meta:
        model = Scene
        fields = ('name', 'text')
