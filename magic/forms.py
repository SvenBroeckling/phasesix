from django import forms

from magic.models import Spell


class SpellForm(forms.ModelForm):
    class Meta:
        model = Spell
        exclude = ('created_by',)
