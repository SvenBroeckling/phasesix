from django import forms
from django.core.exceptions import ValidationError

from .models import (
    EssentialAncestry,
    EssentialArmorProfile,
    EssentialBond,
    EssentialCharacter,
    EssentialCharacterArmor,
    EssentialCharacterItem,
    EssentialCharacterSkill,
    EssentialCharacterSpell,
    EssentialCharacterWeapon,
    EssentialMagicAspectProfile,
    EssentialPath,
    EssentialSkill,
    EssentialSpellProfile,
    EssentialWeaponProfile,
)
from .rules import ATTRIBUTES, magic_slots, valid_skill_distribution


class EssentialCharacterForm(forms.ModelForm):
    skill_names = forms.CharField(help_text="One skill per line.", widget=forms.Textarea(attrs={"rows": 9}))
    skill_ranks = forms.CharField(help_text="One rank per line.", widget=forms.Textarea(attrs={"rows": 9}))
    weapon_profiles = forms.ModelMultipleChoiceField(queryset=EssentialWeaponProfile.objects.all(), required=False)
    armor_profiles = forms.ModelMultipleChoiceField(queryset=EssentialArmorProfile.objects.all(), required=False)
    item_profiles = forms.ModelMultipleChoiceField(queryset=EssentialCharacter._meta.get_field("items").remote_field.model.objects.all(), required=False)
    magic_aspect_profiles = forms.ModelMultipleChoiceField(queryset=EssentialMagicAspectProfile.objects.all(), required=False)
    spell_profiles = forms.ModelMultipleChoiceField(queryset=EssentialSpellProfile.objects.all(), required=False)

    class Meta:
        model = EssentialCharacter
        fields = (
            "name", "birth_date", "century", "player_name", "concept",
            "ancestry", "ancestry_custom", "path", "path_custom", "bond", "bond_custom",
            *ATTRIBUTES, "oath_or_debt", "focus", "regeneration_ritual", "notes", "image",
        )

    def __init__(self, *args, campaign=None, plot=None, **kwargs):
        self.campaign = campaign
        self.plot = plot
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned = super().clean()
        names = [value.strip() for value in cleaned.get("skill_names", "").splitlines() if value.strip()]
        try:
            ranks = [int(value.strip()) for value in cleaned.get("skill_ranks", "").splitlines() if value.strip()]
        except ValueError:
            raise ValidationError("Skill ranks must be numbers.")
        if len(names) != len(ranks) or not valid_skill_distribution(ranks):
            raise ValidationError("Skills require one rank 3, three rank 2, and all remaining ranks at 1.")
        if len(set(name.casefold() for name in names)) != len(names):
            raise ValidationError("Skills must be unique.")
        slots = magic_slots(cleaned.get("gift", 0))
        if len(cleaned.get("magic_aspect_profiles", ())) > slots["aspects"] or len(cleaned.get("spell_profiles", ())) > slots["spells"]:
            raise ValidationError("The supernatural selections exceed the slots granted by Gift.")
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
        EssentialCharacterWeapon.objects.filter(character=character).delete()
        EssentialCharacterArmor.objects.filter(character=character).delete()
        EssentialCharacterItem.objects.filter(character=character).delete()
        EssentialCharacterSpell.objects.filter(character=character).delete()
        for name, rank in self.cleaned_data["_skills"]:
            skill, _ = EssentialSkill.objects.get_or_create(name=name)
            EssentialCharacterSkill.objects.create(character=character, skill=skill, rank=rank)
        for profile in self.cleaned_data["weapon_profiles"]:
            EssentialCharacterWeapon.objects.create(character=character, profile=profile, slot="primary")
        for profile in self.cleaned_data["armor_profiles"]:
            EssentialCharacterArmor.objects.create(character=character, profile=profile)
        for item in self.cleaned_data["item_profiles"]:
            EssentialCharacterItem.objects.create(character=character, item=item)
        character.magic_aspects.set(self.cleaned_data["magic_aspect_profiles"])
        for profile in self.cleaned_data["spell_profiles"]:
            EssentialCharacterSpell.objects.create(character=character, profile=profile)
        return character
