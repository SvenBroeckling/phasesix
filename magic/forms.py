from django import forms
from django.utils.translation import ugettext_lazy as _

from magic.models import Spell


class SpellForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field_name in self.fields:
            field = self.fields.get(field_name)
            if field and isinstance(field , forms.ModelChoiceField):
                field.empty_label = None

    class Meta:
        model = Spell
        exclude = ('created_by',)
        widgets = {
            'description': forms.Textarea(
                attrs={
                    'rows': 4,
                    'placeholder': _('Description / Additional Rules'),
                }),
        }
