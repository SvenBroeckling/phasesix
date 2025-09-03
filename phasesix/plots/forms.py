from plots.models import Plot
from django import forms

from portal.widgets import BootstrapTextarea


class PlotForm(forms.ModelForm):
    class Meta:
        model = Plot
        fields = ("name", "gm_description", "player_abstract", "image")
        widgets = {
            "gm_description": BootstrapTextarea({"rows": 5}),
            "player_abstract": BootstrapTextarea({"rows": 5}),
        }
