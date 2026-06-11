from django import forms
from django.core.exceptions import ValidationError
from django.urls import reverse_lazy
from django.utils.translation import get_language
from django.utils.translation import gettext_lazy as _

from armory.models import Item, RiotGear, Weapon
from magic.models import BaseSpell, SpellOrigin

from .models import (
    EssentialAncestry,
    EssentialBond,
    EssentialCharacter,
    EssentialCharacterSkill,
    EssentialPath,
)
from .rules import (
    ATTRIBUTES,
    magic_slots,
    valid_attribute_distribution,
    valid_skill_distribution,
)

ATTRIBUTE_LABELS = {
    "mind": _("Mind"),
    "will": _("Will"),
    "instinct": _("Instinct"),
    "dexterity": _("Dexterity"),
    "body": _("Body"),
    "presence": _("Presence"),
    "gift": _("Gift"),
    "perception": _("Perception"),
}
RANK_CHOICES = tuple((value, value) for value in range(4))
SKILL_COUNT = 9
TIRAKAN_MONTH_NAMES = {
    "de": (
        "Schneemond",
        "Festmond",
        "Frühlingsmond",
        "Hagelmond",
        "Lebensmond",
        "Sommermond",
        "Obstmond",
        "Haumond",
        "Herbstmond",
        "Weinmond",
        "Nebelmond",
        "Wintermond",
    ),
    "en": (
        "Snowmoon",
        "Feastmoon",
        "Springmoon",
        "Hailmoon",
        "Lifemoon",
        "Summermoon",
        "Orchardmoon",
        "Wheatmoon",
        "Fallmoon",
        "Winemoon",
        "Fogmoon",
        "Wintermoon",
    ),
}


class TirakanBirthDateInput(forms.TextInput):
    template_name = "essential_characters/widgets/tirakan_birth_date.html"

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        language = (get_language() or "en").split("-")[0]
        context["widget"]["month_names"] = TIRAKAN_MONTH_NAMES.get(
            language, TIRAKAN_MONTH_NAMES["en"]
        )
        context["widget"][
            "month_list_id"
        ] = f"{context['widget']['attrs']['id']}_months"
        return context


class CircleRadioSelect(forms.RadioSelect):
    option_template_name = "essential_characters/widgets/circle_radio_option.html"

    def __init__(self, *args, **kwargs):
        attrs = kwargs.setdefault("attrs", {})
        attrs["class"] = f"{attrs.get('class', '')} essential-rank-input".strip()
        super().__init__(*args, **kwargs)


class ConceptForm(forms.Form):
    name = forms.CharField(max_length=80)
    concept = forms.CharField(widget=forms.Textarea(attrs={"rows": 3}))
    oath_or_debt = forms.CharField(
        required=False, widget=forms.Textarea(attrs={"rows": 5})
    )
    birth_date = forms.CharField(
        max_length=40,
        required=False,
        help_text=_("Free text. Tirakan month names are available as suggestions."),
        widget=TirakanBirthDateInput,
    )
    century = forms.TypedChoiceField(
        choices=tuple((value, value) for value in range(1, 11)), coerce=int
    )


class AttributesForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for attribute in ATTRIBUTES:
            self.fields[attribute] = forms.TypedChoiceField(
                label=ATTRIBUTE_LABELS[attribute],
                choices=RANK_CHOICES,
                coerce=int,
                initial=0,
                widget=CircleRadioSelect,
            )

    def clean(self):
        cleaned = super().clean()
        if len(cleaned) == len(ATTRIBUTES) and not valid_attribute_distribution(
            [cleaned[name] for name in ATTRIBUTES]
        ):
            raise ValidationError(
                _(
                    "Choose exactly one attribute at 3, two at 2, three at 1, and two at 0."
                )
            )
        return cleaned


class MarksForm(forms.Form):
    ancestry = forms.ModelChoiceField(queryset=EssentialAncestry.objects.all())
    path = forms.ModelChoiceField(queryset=EssentialPath.objects.all())
    bond = forms.ModelChoiceField(queryset=EssentialBond.objects.all())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            target = f"#summary-{self[name].id_for_label}"
            field.widget.attrs.update(
                {
                    "hx-get": reverse_lazy("essential_characters:mark_summary"),
                    "hx-trigger": "change, load",
                    "hx-target": target,
                    "hx-swap": "innerHTML",
                    "hx-indicator": target,
                }
            )


class SkillsForm(forms.Form):
    def __init__(self, *args, path=None, **kwargs):
        super().__init__(*args, **kwargs)
        suggestions = []
        if path and path.skills:
            suggestions = [
                skill.strip() for skill in path.skills.split(",") if skill.strip()
            ]
        for index in range(SKILL_COUNT):
            self.fields[f"skill_{index}_name"] = forms.CharField(
                label=_("Skill %(number)s") % {"number": index + 1},
                initial=suggestions[index] if index < len(suggestions) else "",
            )
            self.fields[f"skill_{index}_rank"] = forms.TypedChoiceField(
                label=_("Rank"),
                choices=((1, 1), (2, 2), (3, 3)),
                coerce=int,
                initial=1,
                widget=CircleRadioSelect,
            )

    def clean(self):
        cleaned = super().clean()
        names = [
            cleaned.get(f"skill_{index}_name", "").strip()
            for index in range(SKILL_COUNT)
        ]
        ranks = [cleaned.get(f"skill_{index}_rank") for index in range(SKILL_COUNT)]
        if any(not name for name in names):
            raise ValidationError(_("Enter all nine skills."))
        if len(set(name.casefold() for name in names)) != len(names):
            raise ValidationError(_("Skills must be unique."))
        if all(rank is not None for rank in ranks) and not valid_skill_distribution(
            ranks
        ):
            raise ValidationError(
                _(
                    "Choose exactly one skill at rank 3, three at rank 2, and all remaining skills at rank 1."
                )
            )
        cleaned["skills"] = list(zip(names, ranks))
        return cleaned


class EquipmentForm(forms.Form):
    primary_weapon = forms.ModelChoiceField(
        queryset=Weapon.objects.filter(essential_enabled=True), required=False
    )
    secondary_weapon = forms.ModelChoiceField(
        queryset=Weapon.objects.filter(essential_enabled=True), required=False
    )
    armor = forms.ModelChoiceField(
        queryset=RiotGear.objects.filter(essential_enabled=True), required=False
    )
    items = forms.ModelMultipleChoiceField(
        queryset=Item.objects.filter(essential_enabled=True),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            target = f"#summary-{self[name].id_for_label}"
            field.widget.attrs.update(
                {
                    "hx-get": reverse_lazy("essential_characters:equipment_summary"),
                    "hx-trigger": "change, load",
                    "hx-target": target,
                    "hx-swap": "innerHTML",
                    "hx-indicator": target,
                }
            )


class SupernaturalForm(forms.Form):
    focus = forms.CharField(max_length=200, required=False)
    regeneration_ritual = forms.CharField(
        required=False, widget=forms.Textarea(attrs={"rows": 4})
    )
    magic_aspects = forms.ModelMultipleChoiceField(
        queryset=SpellOrigin.objects.filter(essential_enabled=True), required=False
    )
    spells = forms.ModelMultipleChoiceField(
        queryset=BaseSpell.objects.filter(essential_enabled=True), required=False
    )

    def __init__(self, *args, gift=0, **kwargs):
        self.gift = gift
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned = super().clean()
        slots = magic_slots(self.gift)
        aspects = cleaned.get("magic_aspects", ())
        spells = cleaned.get("spells", ())
        if len(aspects) > slots["aspects"] or len(spells) > slots["spells"]:
            raise ValidationError(
                _("The supernatural selections exceed the slots granted by Gift.")
            )
        if any(spell.origin_id and spell.origin not in aspects for spell in spells):
            raise ValidationError(
                _("Selected spells must belong to a selected magic aspect.")
            )
        return cleaned


class EssentialCharacterForm(forms.ModelForm):
    """Full edit form. Creation uses the stricter multi-step wizard forms."""

    skill_names = forms.CharField(widget=forms.Textarea(attrs={"rows": 9}))
    skill_ranks = forms.CharField(widget=forms.Textarea(attrs={"rows": 9}))
    weapons = forms.ModelMultipleChoiceField(
        queryset=Weapon.objects.filter(essential_enabled=True), required=False
    )
    armor = forms.ModelMultipleChoiceField(
        queryset=RiotGear.objects.filter(essential_enabled=True), required=False
    )
    items = forms.ModelMultipleChoiceField(
        queryset=Item.objects.filter(essential_enabled=True),
        required=False,
    )
    magic_aspects = forms.ModelMultipleChoiceField(
        queryset=SpellOrigin.objects.filter(essential_enabled=True), required=False
    )
    spells = forms.ModelMultipleChoiceField(
        queryset=BaseSpell.objects.filter(essential_enabled=True), required=False
    )

    class Meta:
        model = EssentialCharacter
        fields = (
            "name",
            "birth_date",
            "century",
            "concept",
            "ancestry",
            "path",
            "bond",
            *ATTRIBUTES,
            "oath_or_debt",
            "focus",
            "regeneration_ritual",
            "notes",
            "image",
        )

    def __init__(self, *args, campaign=None, plot=None, **kwargs):
        self.campaign = campaign
        self.plot = plot
        super().__init__(*args, **kwargs)
        self.fields["birth_date"].widget = TirakanBirthDateInput()
        self.fields["birth_date"].help_text = _(
            "Free text. Tirakan month names are available as suggestions."
        )
        for attribute in ATTRIBUTES:
            self.fields[attribute].widget = CircleRadioSelect(choices=RANK_CHOICES)
        if self.instance.pk:
            for field_name in ("weapons", "armor", "items", "magic_aspects", "spells"):
                self.fields[field_name].initial = getattr(
                    self.instance, field_name
                ).all()

    def clean(self):
        cleaned = super().clean()
        names = [
            value.strip()
            for value in cleaned.get("skill_names", "").splitlines()
            if value.strip()
        ]
        try:
            ranks = [
                int(value.strip())
                for value in cleaned.get("skill_ranks", "").splitlines()
                if value.strip()
            ]
        except ValueError as error:
            raise ValidationError(_("Skill ranks must be numbers.")) from error
        if len(names) != len(ranks) or not valid_skill_distribution(ranks):
            raise ValidationError(
                _(
                    "Skills require one rank 3, three rank 2, and all remaining ranks at 1."
                )
            )
        if len(set(name.casefold() for name in names)) != len(names):
            raise ValidationError(_("Skills must be unique."))
        slots = magic_slots(cleaned.get("gift", 0))
        if (
            len(cleaned.get("magic_aspects", ())) > slots["aspects"]
            or len(cleaned.get("spells", ())) > slots["spells"]
        ):
            raise ValidationError(
                _("The supernatural selections exceed the slots granted by Gift.")
            )
        aspects = cleaned.get("magic_aspects", ())
        if any(
            spell.origin_id and spell.origin not in aspects
            for spell in cleaned.get("spells", ())
        ):
            raise ValidationError(
                _("Selected spells must belong to a selected magic aspect.")
            )
        cleaned["_skills"] = list(zip(names, ranks))
        return cleaned

    def save(self, commit=True):
        character = super().save(commit=False)
        character.campaign = self.campaign
        character.plot = self.plot
        if not commit:
            return character
        character.save()
        EssentialCharacterSkill.objects.filter(character=character).delete()
        for name, rank in self.cleaned_data["_skills"]:
            EssentialCharacterSkill.objects.create(
                character=character, name=name, rank=rank
            )
        character.weapons.set(self.cleaned_data["weapons"])
        character.armor.set(self.cleaned_data["armor"])
        character.items.set(self.cleaned_data["items"])
        character.magic_aspects.set(self.cleaned_data["magic_aspects"])
        character.spells.set(self.cleaned_data["spells"])
        return character
