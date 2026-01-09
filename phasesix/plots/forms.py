from plots.models import Plot, PlotElement, Handout, Location
from characters.models import Character
from django import forms
from django.utils.translation import gettext as _

from portal.widgets import BootstrapTextarea


class PlotForm(forms.ModelForm):
    class Meta:
        model = Plot
        fields = (
            "name",
            "epoch_extension",
            "world_extension",
            "extensions",
            "gm_description",
            "player_abstract",
            "image",
            "language",
        )
        widgets = {
            "gm_description": BootstrapTextarea({"rows": 20}),
            "player_abstract": BootstrapTextarea({"rows": 20}),
        }


class PlotElementForm(forms.ModelForm):
    class Meta:
        model = PlotElement
        fields = ("name", "gm_notes", "player_summary")
        widgets = {
            "gm_notes": BootstrapTextarea({"rows": 15}),
            "player_summary": BootstrapTextarea({"rows": 15}),
        }


class HandoutForm(forms.ModelForm):
    class Meta:
        model = Handout
        fields = ("name", "description", "image")
        widgets = {
            "description": BootstrapTextarea({"rows": 5}),
        }


class LocationForm(forms.ModelForm):
    class Meta:
        model = Location
        fields = ("name", "description", "image")
        widgets = {
            "description": BootstrapTextarea({"rows": 5}),
        }


class PlotNpcForm(forms.ModelForm):
    class Meta:
        model = Character
        fields = ("name", "description", "image")
        widgets = {
            "description": BootstrapTextarea({"rows": 5}),
        }


class PlotFromDescriptionForm(forms.Form):
    description = forms.CharField(
        label=_("Plot description"),
        widget=BootstrapTextarea({"rows": 12}),
        required=True,
    )
    language = forms.ChoiceField(
        label=_("Language"),
        choices=(
            ("en", _("English")),
            ("de", _("German")),
        ),
        required=True,
    )
