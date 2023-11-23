from django import forms

from worlds.models import WikiPage


class WikiPageForm(forms.ModelForm):
    class Meta:
        model = WikiPage
        fields = [
            "name_de",
            "name_en",
            "text_de",
            "text_en",
        ]


class WikiPageTextForm(forms.ModelForm):
    class Meta:
        model = WikiPage
        fields = [
            "text_de",
            "text_en",
        ]
        widgets = {
            "text_de": forms.Textarea(attrs={"style": "height: 75vh"}),
            "text_en": forms.Textarea(attrs={"style": "height: 75vh"}),
        }
