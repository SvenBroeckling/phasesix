from django import forms

from characters.models import Character


class CharacterImageForm(forms.ModelForm):
    class Meta:
        model = Character
        fields = ('image', 'name')
