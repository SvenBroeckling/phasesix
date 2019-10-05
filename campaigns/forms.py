from django import forms

from campaigns.models import Scene


class SceneForm(forms.ModelForm):
    class Meta:
        model = Scene
        fields = ('name', 'text')
