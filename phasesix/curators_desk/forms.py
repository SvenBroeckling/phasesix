from django import forms
from django.core.exceptions import FieldDoesNotExist
from django.utils.translation import gettext_lazy as _

from armory.models import Weapon, RiotGear
from homebrew.forms import (
    CreateItemForm,
    CreateRiotGearForm,
    CreateWeaponForm,
    CreateBaseSpellForm,
    CreateBodyModificationForm,
    CreateTemplateForm,
    CreateQuirkForm,
    CreateLanguageForm,
    CreateFoeForm,
    CreateRecipeForm,
)
from rulebook.models import Chapter

COVER_CHOICES = (
    (7, _("no cover")),
    (4, "4+"),
    (5, "5+"),
    (6, "6+"),
)


class CombatSimDummyForm(forms.Form):
    weapon = forms.ModelChoiceField(Weapon.objects.all(), label=_("Weapon"))
    riot_gear = forms.ModelChoiceField(
        RiotGear.objects.all(), label=_("Armor"), required=False
    )
    attack_value = forms.IntegerField(label=_("Attack value"))
    cover = forms.ChoiceField(label=_("Cover"), choices=COVER_CHOICES)
    health = forms.IntegerField(label=_("Health"))


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


HOME_BREW_CREATE_FORMS = (
    CreateItemForm,
    CreateRiotGearForm,
    CreateWeaponForm,
    CreateBaseSpellForm,
    CreateBodyModificationForm,
    CreateTemplateForm,
    CreateQuirkForm,
    CreateLanguageForm,
    CreateFoeForm,
    CreateRecipeForm,
)

HOME_BREW_CREATE_FORM_BY_MODEL = {
    form_class._meta.model: form_class for form_class in HOME_BREW_CREATE_FORMS
}
HOME_BREW_REVIEW_FORM_CACHE = {}


def _build_homebrew_review_fields(form_class):
    model = form_class._meta.model
    fields = list(form_class._meta.fields)
    expanded_fields = []
    for field in fields:
        expanded_fields.append(field)
        if not field.endswith("_de"):
            continue
        english_field = f"{field[:-3]}_en"
        if english_field in expanded_fields:
            continue
        try:
            model._meta.get_field(english_field)
        except FieldDoesNotExist:
            continue
        expanded_fields.append(english_field)
    if "extensions" not in expanded_fields:
        try:
            model._meta.get_field("extensions")
        except FieldDoesNotExist:
            pass
        else:
            expanded_fields.append("extensions")
    return expanded_fields


def get_homebrew_review_form_class(model):
    if model in HOME_BREW_REVIEW_FORM_CACHE:
        return HOME_BREW_REVIEW_FORM_CACHE[model]
    create_form_class = HOME_BREW_CREATE_FORM_BY_MODEL.get(model)
    if not create_form_class:
        return None
    fields = _build_homebrew_review_fields(create_form_class)
    meta_kwargs = {"fields": fields}
    help_texts = getattr(create_form_class._meta, "help_texts", None)
    if help_texts:
        meta_kwargs["help_texts"] = help_texts
    labels = getattr(create_form_class._meta, "labels", None)
    if labels:
        meta_kwargs["labels"] = labels
    form_class = forms.modelform_factory(model, **meta_kwargs)
    HOME_BREW_REVIEW_FORM_CACHE[model] = form_class
    return form_class
