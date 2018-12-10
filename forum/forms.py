from django import forms
from django.utils.translation import ugettext_lazy as _


class NewThreadForm(forms.Form):
    name = forms.CharField(max_length=60, label=_('Name'), required=True)
    text = forms.CharField(widget=forms.Textarea, label=_('Text'), required=True)


class NewPostForm(forms.Form):
    text = forms.CharField(widget=forms.Textarea, label=_('Text'), required=True)
