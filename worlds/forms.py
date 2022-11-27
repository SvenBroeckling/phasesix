from django import forms

from worlds.models import WikiPage


class WikiPageForm(forms.ModelForm):
    class Meta:
        model = WikiPage
        fields = [
            'name_de',
            'name_en',
            'abstract_de',
            'abstract_en',
        ]


class WikiPageTextForm(forms.ModelForm):
    class Meta:
        model = WikiPage
        fields = [
            'text_de',
            'text_en',
        ]
        widgets = {
            'text_de': forms.Textarea(attrs={'rows': 40}),
            'text_en': forms.Textarea(attrs={'rows': 40})
        }
