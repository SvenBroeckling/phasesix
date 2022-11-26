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
