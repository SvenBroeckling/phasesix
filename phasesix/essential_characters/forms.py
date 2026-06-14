from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.urls import reverse_lazy
from django.utils.translation import get_language
from django.utils.translation import gettext_lazy as _

from armory.models import (
    Item,
    ItemType,
    RiotGear,
    RiotGearType,
    Weapon,
    WeaponType,
)
from magic.models import BaseSpell, SpellOrigin
from rules.models import Extension, Lineage, Template

from .models import (
    EssentialBond,
    EssentialCharacter,
    EssentialCharacterSkill,
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
ESSENTIAL_ITEM_EXTENSION_IDENTIFIERS = ("tirakan", "middleages")


def essential_mark_queryset(model, *, user=None, campaign=None):
    queryset = (
        model.objects.filter(essential_enabled=True)
        if model is not EssentialBond
        else model.objects.all()
    )
    visibility = Q(is_homebrew=False)
    if user and user.is_authenticated:
        visibility |= Q(created_by=user)
    if campaign:
        visibility |= Q(homebrew_campaign=campaign)
    return queryset.filter(visibility).distinct()


def essential_item_queryset():
    return Item.objects.filter(
        Q(extensions__identifier__in=ESSENTIAL_ITEM_EXTENSION_IDENTIFIERS)
        | Q(extensions__in=Extension.objects.filter(is_mandatory=True))
    ).distinct()


def essential_equipment_queryset(model, *, user=None, campaign=None):
    queryset = (
        essential_item_queryset()
        if model is Item
        else model.objects.filter(essential_enabled=True)
    )
    visibility = Q(is_homebrew=False)
    if user and user.is_authenticated:
        visibility |= Q(created_by=user)
    if campaign:
        visibility |= Q(homebrew_campaign=campaign)
    return queryset.filter(visibility).distinct()


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


class SearchableItemSelectMultiple(forms.SelectMultiple):
    template_name = "essential_characters/widgets/searchable_item_select.html"

    def __init__(self, *args, **kwargs):
        attrs = kwargs.setdefault("attrs", {})
        attrs["class"] = f"{attrs.get('class', '')} d-none".strip()
        super().__init__(*args, **kwargs)


class SearchableSpellSelect(forms.Select):
    template_name = "essential_characters/widgets/searchable_spell_select.html"

    def __init__(self, *args, **kwargs):
        attrs = kwargs.setdefault("attrs", {})
        attrs["class"] = f"{attrs.get('class', '')} d-none".strip()
        super().__init__(*args, **kwargs)

    def create_option(self, name, value, label, selected, index, **kwargs):
        option = super().create_option(name, value, label, selected, index, **kwargs)
        if value:
            option["attrs"]["data-origin"] = str(value.instance.origin_id or "")
        return option


class AjaxSearchSelectMultiple(forms.SelectMultiple):
    template_name = "essential_characters/widgets/ajax_search_select_multiple.html"

    def __init__(self, *args, search_type, **kwargs):
        self.search_type = search_type
        attrs = kwargs.setdefault("attrs", {})
        attrs["class"] = f"{attrs.get('class', '')} d-none".strip()
        attrs["data-search-type"] = search_type
        super().__init__(*args, **kwargs)

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        selected_values = {str(item) for item in value or ()}
        for _, options, _ in context["widget"]["optgroups"]:
            options[:] = [
                option for option in options if str(option["value"]) in selected_values
            ]
        context["widget"]["search_type"] = self.search_type
        context["widget"]["search_url"] = context["widget"]["attrs"].get(
            "data-search-url", ""
        )
        return context


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
    ancestry = forms.ModelChoiceField(
        queryset=Lineage.objects.filter(essential_enabled=True)
    )
    path = forms.ModelChoiceField(
        queryset=Template.objects.filter(essential_enabled=True)
    )
    bond = forms.ModelChoiceField(queryset=EssentialBond.objects.all())

    def __init__(self, *args, user=None, campaign=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["ancestry"].queryset = essential_mark_queryset(
            Lineage, user=user, campaign=campaign
        )
        self.fields["path"].queryset = essential_mark_queryset(
            Template, user=user, campaign=campaign
        )
        self.fields["bond"].queryset = essential_mark_queryset(
            EssentialBond, user=user, campaign=campaign
        )
        for name, field in self.fields.items():
            target = f"#summary-{self[name].id_for_label}"
            summary_url = reverse_lazy("essential_characters:mark_summary")
            if campaign:
                summary_url = f"{summary_url}?campaign={campaign.pk}"
            field.widget.attrs.update(
                {
                    "hx-get": summary_url,
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
        if path and path.essential_skills:
            suggestions = [
                skill.strip()
                for skill in path.essential_skills.split(",")
                if skill.strip()
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
        queryset=essential_item_queryset(),
        required=False,
        widget=SearchableItemSelectMultiple,
    )

    def __init__(self, *args, user=None, campaign=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["primary_weapon"].queryset = essential_equipment_queryset(
            Weapon, user=user, campaign=campaign
        )
        self.fields["secondary_weapon"].queryset = essential_equipment_queryset(
            Weapon, user=user, campaign=campaign
        )
        self.fields["armor"].queryset = essential_equipment_queryset(
            RiotGear, user=user, campaign=campaign
        )
        self.fields["items"].queryset = essential_equipment_queryset(
            Item, user=user, campaign=campaign
        )
        for name, field in self.fields.items():
            if name == "items":
                continue
            target = f"#summary-{self[name].id_for_label}"
            summary_url = reverse_lazy("essential_characters:equipment_summary")
            if campaign:
                summary_url = f"{summary_url}?campaign={campaign.pk}"
            field.widget.attrs.update(
                {
                    "hx-get": summary_url,
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

    def __init__(self, *args, gift=0, **kwargs):
        self.gift = gift
        super().__init__(*args, **kwargs)
        slots = magic_slots(gift)
        for index in range(slots["aspects"]):
            name = f"magic_aspect_{index}"
            self.fields[name] = forms.ModelChoiceField(
                label=_("Magic aspect %(number)s") % {"number": index + 1},
                queryset=SpellOrigin.objects.all(),
                required=False,
            )
            target = f"#summary-{self[name].id_for_label}"
            self.fields[name].widget.attrs.update(
                {
                    "hx-get": reverse_lazy("essential_characters:supernatural_summary"),
                    "hx-trigger": "change, load",
                    "hx-target": target,
                    "hx-swap": "innerHTML",
                    "hx-indicator": target,
                }
            )
        for index in range(slots["spells"]):
            name = f"spell_{index}"
            self.fields[name] = forms.ModelChoiceField(
                label=_("Spell %(number)s") % {"number": index + 1},
                queryset=BaseSpell.objects.select_related("origin"),
                required=False,
                empty_label=_("Search spells"),
                widget=SearchableSpellSelect,
            )
            target = f"#summary-{self[name].id_for_label}"
            self.fields[name].widget.attrs.update(
                {
                    "hx-get": reverse_lazy("essential_characters:supernatural_summary"),
                    "hx-trigger": "change, load",
                    "hx-target": target,
                    "hx-swap": "innerHTML",
                    "hx-indicator": target,
                }
            )

    def clean(self):
        cleaned = super().clean()
        slots = magic_slots(self.gift)
        aspects = [
            cleaned.get(f"magic_aspect_{index}") for index in range(slots["aspects"])
        ]
        spells = [cleaned.get(f"spell_{index}") for index in range(slots["spells"])]
        aspects = [aspect for aspect in aspects if aspect]
        spells = [spell for spell in spells if spell]
        if len(set(aspects)) != len(aspects) or len(set(spells)) != len(spells):
            raise ValidationError(_("Supernatural selections must be unique."))
        if any(not spell.origin_id or spell.origin not in aspects for spell in spells):
            raise ValidationError(
                _("Selected spells must belong to a selected magic aspect.")
            )
        cleaned["magic_aspects"] = aspects
        cleaned["spells"] = spells
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
        queryset=essential_item_queryset(),
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
        EssentialCharacterSkill.replace_for_character(
            character, self.cleaned_data["_skills"]
        )
        character.weapons.set(self.cleaned_data["weapons"])
        character.armor.set(self.cleaned_data["armor"])
        character.items.set(self.cleaned_data["items"])
        character.magic_aspects.set(self.cleaned_data["magic_aspects"])
        character.spells.set(self.cleaned_data["spells"])
        return character


class EssentialCharacterImageForm(forms.ModelForm):
    class Meta:
        model = EssentialCharacter
        fields = ("image",)


class EssentialIdentityEditForm(forms.ModelForm):
    class Meta:
        model = EssentialCharacter
        fields = ("name", "concept", "birth_date", "century", "oath_or_debt")
        widgets = {
            "concept": forms.Textarea(attrs={"rows": 3}),
            "oath_or_debt": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["birth_date"].widget = TirakanBirthDateInput()


class EssentialMarksEditForm(forms.ModelForm):
    class Meta:
        model = EssentialCharacter
        fields = ("ancestry", "path", "bond")

    ancestry = forms.ModelChoiceField(
        queryset=Lineage.objects.filter(essential_enabled=True)
    )
    path = forms.ModelChoiceField(
        queryset=Template.objects.filter(essential_enabled=True)
    )
    bond = forms.ModelChoiceField(queryset=EssentialBond.objects.all())

    def __init__(self, *args, user=None, campaign=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["ancestry"].queryset = essential_mark_queryset(
            Lineage, user=user, campaign=campaign
        )
        self.fields["path"].queryset = essential_mark_queryset(
            Template, user=user, campaign=campaign
        )
        self.fields["bond"].queryset = essential_mark_queryset(
            EssentialBond, user=user, campaign=campaign
        )


class EssentialCustomMarkForm(forms.Form):
    name = forms.CharField(label=_("Name"), max_length=160)
    description = forms.CharField(
        label=_("Description"), max_length=500, widget=forms.Textarea(attrs={"rows": 3})
    )
    benefit = forms.CharField(label=_("Benefit"), max_length=255)
    vulnerability = forms.CharField(label=_("Vulnerability"), max_length=255)
    skills = forms.CharField(
        label=_("Skills"),
        max_length=500,
        required=False,
        help_text=_("Comma-separated skill suggestions."),
    )
    facet = forms.CharField(label=_("Path facet"), max_length=255, required=False)
    translate_with_openai = forms.BooleanField(
        label=_("Translate German and English with OpenAI"),
        required=False,
        initial=True,
    )

    def __init__(self, *args, mark_type, user, **kwargs):
        super().__init__(*args, **kwargs)
        self.mark_type = mark_type
        self.fields["name"].max_length = {
            "ancestry": 80,
            "path": 120,
            "bond": 160,
        }[mark_type]
        self.fields["name"].widget.attrs["maxlength"] = self.fields["name"].max_length
        if mark_type == "bond":
            self.fields.pop("skills")
            self.fields.pop("facet")
        elif mark_type == "ancestry":
            self.fields.pop("facet")
        if not user.is_staff:
            self.fields.pop("translate_with_openai")


class EssentialAttributesEditForm(forms.ModelForm):
    class Meta:
        model = EssentialCharacter
        fields = ATTRIBUTES

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for attribute in ATTRIBUTES:
            self.fields[attribute].widget = CircleRadioSelect(choices=RANK_CHOICES)

    def clean(self):
        cleaned = super().clean()
        slots = magic_slots(cleaned.get("gift", self.instance.gift))
        if (
            self.instance.magic_aspects.count() > slots["aspects"]
            or self.instance.spells.count() > slots["spells"]
        ):
            raise ValidationError(
                _("The supernatural selections exceed the slots granted by Gift.")
            )
        return cleaned


class EssentialSkillsEditForm(forms.Form):
    def __init__(self, *args, character, **kwargs):
        self.character = character
        super().__init__(*args, **kwargs)
        assignments = list(character.essentialcharacterskill_set.all())
        for index in range(SKILL_COUNT):
            assignment = assignments[index] if index < len(assignments) else None
            self.fields[f"skill_{index}_name"] = forms.CharField(
                label=_("Skill %(number)s") % {"number": index + 1},
                initial=assignment.name if assignment else "",
            )
            self.fields[f"skill_{index}_rank"] = forms.TypedChoiceField(
                label=_("Rank"),
                choices=tuple((value, value) for value in range(5)),
                coerce=int,
                initial=assignment.rank if assignment else 1,
                widget=CircleRadioSelect(
                    choices=tuple((value, value) for value in range(5))
                ),
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
        cleaned["skills"] = list(zip(names, ranks))
        return cleaned

    def save(self):
        EssentialCharacterSkill.replace_for_character(
            self.character, self.cleaned_data["skills"]
        )


class EssentialAddSkillForm(forms.Form):
    name = forms.CharField(label=_("Name"), max_length=160)
    rank = forms.TypedChoiceField(
        label=_("Rank"),
        choices=((1, 1), (2, 2), (3, 3)),
        coerce=int,
        initial=1,
        widget=CircleRadioSelect,
    )


class EssentialCustomEquipmentForm(forms.Form):
    name = forms.CharField(label=_("Name"), max_length=256)
    description = forms.CharField(
        label=_("Description"),
        required=False,
        widget=forms.Textarea(attrs={"rows": 3}),
    )
    type = forms.ModelChoiceField(label=_("Type"), queryset=ItemType.objects.none())
    damage = forms.CharField(label=_("Damage"), max_length=40, required=False)
    range = forms.CharField(label=_("Range"), max_length=80, required=False)
    grip = forms.CharField(label=_("Grip"), max_length=40, required=False)
    protection = forms.CharField(label=_("Protection"), max_length=40, required=False)
    load = forms.CharField(label=_("Load"), max_length=40, required=False)
    sealing = forms.CharField(label=_("Sealing"), max_length=40, required=False)
    properties = forms.CharField(label=_("Properties"), max_length=500, required=False)
    translate_with_openai = forms.BooleanField(
        label=_("Translate German and English with OpenAI"),
        required=False,
        initial=True,
    )

    def __init__(self, *args, equipment_type, user, **kwargs):
        super().__init__(*args, **kwargs)
        if equipment_type == "weapon":
            self.fields["type"].queryset = WeaponType.objects.all()
            for name in ("protection", "load", "sealing"):
                self.fields.pop(name)
        elif equipment_type == "armor":
            self.fields["type"].queryset = RiotGearType.objects.all()
            for name in ("damage", "range", "grip"):
                self.fields.pop(name)
        else:
            self.fields["type"].queryset = ItemType.objects.all()
            for name in (
                "damage",
                "range",
                "grip",
                "protection",
                "load",
                "sealing",
                "properties",
            ):
                self.fields.pop(name)
        if not user.is_staff:
            self.fields.pop("translate_with_openai")


class EssentialEquipmentEditForm(forms.ModelForm):
    weapons = forms.ModelMultipleChoiceField(
        queryset=Weapon.objects.filter(essential_enabled=True),
        required=False,
        widget=AjaxSearchSelectMultiple(search_type="weapons"),
    )
    armor = forms.ModelMultipleChoiceField(
        queryset=RiotGear.objects.filter(essential_enabled=True),
        required=False,
        widget=AjaxSearchSelectMultiple(search_type="armor"),
    )
    items = forms.ModelMultipleChoiceField(
        queryset=essential_item_queryset(),
        required=False,
        widget=AjaxSearchSelectMultiple(search_type="items"),
    )

    class Meta:
        model = EssentialCharacter
        fields = ("weapons", "armor", "items")


class EssentialSupernaturalEditForm(forms.ModelForm):
    magic_aspects = forms.ModelMultipleChoiceField(
        queryset=SpellOrigin.objects.all(),
        required=False,
        widget=AjaxSearchSelectMultiple(search_type="magic_aspects"),
    )
    spells = forms.ModelMultipleChoiceField(
        queryset=BaseSpell.objects.select_related("origin"),
        required=False,
        widget=AjaxSearchSelectMultiple(search_type="spells"),
    )

    class Meta:
        model = EssentialCharacter
        fields = (
            "focus",
            "regeneration_ritual",
            "magic_aspects",
            "spells",
        )
        widgets = {"regeneration_ritual": forms.Textarea(attrs={"rows": 4})}

    def clean(self):
        cleaned = super().clean()
        slots = magic_slots(self.instance.gift)
        aspects = cleaned.get("magic_aspects", ())
        spells = cleaned.get("spells", ())
        if len(aspects) > slots["aspects"] or len(spells) > slots["spells"]:
            raise ValidationError(
                _("The supernatural selections exceed the slots granted by Gift.")
            )
        if any(not spell.origin_id or spell.origin not in aspects for spell in spells):
            raise ValidationError(
                _("Selected spells must belong to a selected magic aspect.")
            )
        return cleaned


class EssentialNotesEditForm(forms.ModelForm):
    class Meta:
        model = EssentialCharacter
        fields = ("notes",)
        widgets = {"notes": forms.Textarea(attrs={"rows": 8})}
