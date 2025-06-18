from django import forms
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.utils.translation import gettext_lazy as _

from armory.models import Weapon, RiotGear
from rulebook.models import Chapter

COVER_CHOICES = (
    (7, _('no cover')),
    (4, '4+'),
    (5, '5+'),
    (6, '6+'),
)


class CombatSimDummyForm(forms.Form):
    weapon = forms.ModelChoiceField(Weapon.objects.all(), label=_('Weapon'))
    riot_gear = forms.ModelChoiceField(RiotGear.objects.all(), label=_('Armor'),
                                       required=False)
    attack_value = forms.IntegerField(label=_('Attack value'))
    cover = forms.ChoiceField(label=_('Cover'), choices=COVER_CHOICES)
    health = forms.IntegerField(label=_('Health'))


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = [single_file_clean(data, initial)]
        return result


class UploadRulebookForm(forms.Form):
    markdown_files = MultipleFileField(
        label=_('Markdown files'),
    )

    def save(self, *args, **kwargs):
        for file in self.cleaned_data['markdown_files']:
            file_name, ext = file.name.split(".")
            identifier = "_".join(file_name.split("_")[:-1])
            language = file_name.split("_")[-1]
            chapter = Chapter.objects.get(identifier=f"chapter-{identifier}")
            field = getattr(chapter, f"rules_file_{language}")
            field.save(f"{identifier}_{language}.{ext}", file)
