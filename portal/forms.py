from django import forms
from django.utils.translation import gettext_lazy as _
from django_registration.forms import RegistrationForm


class CustomRegistrationForm(RegistrationForm):
    email2 = forms.CharField(label=_("E-Mail"), max_length=100, required=False)

    def clean_email2(self):
        email2 = self.cleaned_data.get("email2")
        if email2:
            raise forms.ValidationError("Keine Eingabe.")
        return email2
