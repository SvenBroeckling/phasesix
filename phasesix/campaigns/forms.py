from django import forms
from django.utils.translation import gettext_lazy as _

from campaigns.models import Scene, Campaign
from rules.models import Extension


class CreateCampaignExtensionsForm(forms.Form):
    extensions = forms.ModelMultipleChoiceField(
        queryset=Extension.objects.filter(
            type__in=["x", "w"], is_mandatory=False, is_active=True
        ),
        label=_("Extensions"),
        required=False,
        widget=forms.SelectMultiple(attrs={"style": "display: none"}),
    )


class CampaignSettingsIntegrationForm(forms.ModelForm):
    class Meta:
        model = Campaign
        fields = (
            "roll_on_site",
            "tale_spire_integration",
            "discord_integration",
            "discord_webhook_url",
        )


class CampaignSettingsGameForm(forms.ModelForm):
    class Meta:
        model = Campaign
        fields = (
            "name",
            "abstract",
            "currency_map",
            "seed_money",
            "starting_template_points",
            "image",
            "backdrop_image",
        )


class CampaignSettingsVisibilityForm(forms.ModelForm):
    class Meta:
        model = Campaign
        fields = (
            "character_visibility",
            "foe_visibility",
            "npc_visibility",
            "game_log_visibility",
        )


class SceneForm(forms.ModelForm):
    class Meta:
        model = Scene
        fields = ("name", "text")
