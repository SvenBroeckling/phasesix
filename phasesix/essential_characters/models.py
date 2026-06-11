import os
import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.db import models, transaction
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from phasesix.models import ModelWithImage, image_upload_path
from worlds.unique_slugify import unique_slugify
from .rules import ATTRIBUTES, CENTURY_LEVELS, magic_slots, valid_attribute_distribution, valid_skill_distribution


def _copy_file(field_file):
    if not field_file:
        return None
    field_file.open("rb")
    try:
        data = field_file.read()
    finally:
        field_file.close()
    root, filename = os.path.split(field_file.name)
    stem, extension = os.path.splitext(filename)
    return default_storage.save(os.path.join(root, f"{stem}_{uuid.uuid4().hex}{extension}"), ContentFile(data))


class EssentialMark(models.Model):
    name = models.CharField(max_length=160, unique=True)
    benefit = models.TextField(blank=True)
    vulnerability = models.TextField(blank=True)

    class Meta:
        abstract = True
        ordering = ("name",)

    def __str__(self):
        return self.name


class EssentialAncestry(EssentialMark):
    skills = models.TextField(blank=True)


class EssentialPath(EssentialMark):
    facet = models.TextField(blank=True)
    skills = models.TextField(blank=True)


class EssentialBond(EssentialMark):
    pass


class EssentialSkill(models.Model):
    name = models.CharField(max_length=160, unique=True)

    class Meta:
        ordering = ("name",)

    def __str__(self):
        return self.name


class EssentialCharacterQuerySet(models.QuerySet):
    def pc(self):
        return self.filter(npc_campaign__isnull=True)

    def npc(self):
        return self.filter(npc_campaign__isnull=False)

    def for_world(self, world):
        return self.filter(models.Q(campaign__world_extension=world.extension) | models.Q(npc_campaign__world_extension=world.extension)).distinct() if world else self


class EssentialCharacter(ModelWithImage):
    objects = EssentialCharacterQuerySet.as_manager()
    image_upload_to = "essential_character_images"
    slug = models.SlugField(max_length=220, unique=True)
    name = models.CharField(max_length=80)
    birth_date = models.CharField(max_length=40, blank=True)
    century = models.PositiveSmallIntegerField(default=1)
    player_name = models.CharField(max_length=120, blank=True)
    concept = models.TextField(blank=True)
    oath_or_debt = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    image = models.ImageField(upload_to=image_upload_path, max_length=256, blank=True, null=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    is_favorite = models.BooleanField(default=False)
    cloned_from = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL, related_name="clones")
    campaign = models.ForeignKey("campaigns.Campaign", null=True, blank=True, on_delete=models.SET_NULL)
    npc_campaign = models.ForeignKey("campaigns.Campaign", null=True, blank=True, on_delete=models.SET_NULL, related_name="essential_npc_set")
    plot = models.ForeignKey("plots.Plot", null=True, blank=True, on_delete=models.SET_NULL, related_name="essential_plot_npc_set")
    ancestry = models.ForeignKey(EssentialAncestry, null=True, blank=True, on_delete=models.SET_NULL)
    ancestry_custom = models.CharField(max_length=160, blank=True)
    path = models.ForeignKey(EssentialPath, null=True, blank=True, on_delete=models.SET_NULL)
    path_custom = models.CharField(max_length=160, blank=True)
    bond = models.ForeignKey(EssentialBond, null=True, blank=True, on_delete=models.SET_NULL)
    bond_custom = models.CharField(max_length=160, blank=True)
    mind = models.PositiveSmallIntegerField(default=0)
    will = models.PositiveSmallIntegerField(default=0)
    instinct = models.PositiveSmallIntegerField(default=0)
    dexterity = models.PositiveSmallIntegerField(default=0)
    body = models.PositiveSmallIntegerField(default=0)
    presence = models.PositiveSmallIntegerField(default=0)
    gift = models.PositiveSmallIntegerField(default=0)
    perception = models.PositiveSmallIntegerField(default=0)
    wounds = models.PositiveSmallIntegerField(default=0)
    burden = models.PositiveSmallIntegerField(default=0)
    omen = models.PositiveSmallIntegerField(default=0)
    arkana = models.PositiveSmallIntegerField(default=0)
    favor = models.PositiveSmallIntegerField(default=0)
    corruption = models.PositiveSmallIntegerField(default=0)
    focus = models.CharField(max_length=200, blank=True)
    regeneration_ritual = models.TextField(blank=True)
    skills = models.ManyToManyField(EssentialSkill, through="EssentialCharacterSkill")
    magic_aspects = models.ManyToManyField("EssentialMagicAspectProfile", blank=True)
    spells = models.ManyToManyField("EssentialSpellProfile", through="EssentialCharacterSpell", blank=True)
    items = models.ManyToManyField("armory.Item", through="EssentialCharacterItem", blank=True)
    weapons = models.ManyToManyField("EssentialWeaponProfile", through="EssentialCharacterWeapon", blank=True)
    armor = models.ManyToManyField("EssentialArmorProfile", through="EssentialCharacterArmor", blank=True)

    class Meta:
        ordering = ("-is_favorite", "-created_at")

    def __str__(self):
        return self.name

    @property
    def attribute_values(self):
        return [getattr(self, key) for key in ATTRIBUTES]

    def clean(self):
        super().clean()
        if not 1 <= self.century <= 10:
            raise ValidationError({"century": _("Century must be between 1 and 10.")})
        if not valid_attribute_distribution(self.attribute_values):
            raise ValidationError(_("Attributes must use the Essential starting distribution."))
        for field in ("ancestry", "path", "bond"):
            if not getattr(self, f"{field}_id") and not getattr(self, f"{field}_custom"):
                raise ValidationError({f"{field}_custom": _("Select a predefined mark or enter a custom one.")})
        if self.campaign_id and self.npc_campaign_id:
            raise ValidationError(_("A character cannot be both a PC and NPC in a campaign."))
        if self.plot_id and (self.campaign_id or self.npc_campaign_id) and self.plot.campaign_id != (self.campaign_id or self.npc_campaign_id):
            raise ValidationError(_("Character plot and campaign assignments must match."))
        for campaign in filter(None, (self.campaign, self.npc_campaign)):
            if campaign.ruleset != "tirakan_essential" or campaign.world_extension.identifier != "tirakan":
                raise ValidationError(_("Essential characters may only join Tirakan Essential campaigns."))
        if self.plot_id and (self.plot.ruleset != "tirakan_essential" or self.plot.world_extension.identifier != "tirakan"):
            raise ValidationError(_("Essential characters may only join Tirakan Essential plots."))

    def save(self, *args, **kwargs):
        if not self.slug:
            unique_slugify(self, self.name)
        self.full_clean()
        return super().save(*args, **kwargs)

    def validate_assignments(self):
        ranks = list(self.essentialcharacterskill_set.values_list("rank", flat=True))
        if ranks and not valid_skill_distribution(ranks):
            raise ValidationError(_("Skills must contain one rank 3, three rank 2, and all remaining skills at rank 1."))
        slots = magic_slots(self.gift)
        if self.magic_aspects.count() > slots["aspects"] or self.essentialcharacterspell_set.count() > slots["spells"]:
            raise ValidationError(_("The supernatural selections exceed the slots granted by Gift."))

    def may_edit(self, user):
        return self.created_by == user or bool(self.pc_or_npc_campaign and self.pc_or_npc_campaign.may_edit(user))

    @property
    def pc_or_npc_campaign(self):
        return self.campaign or self.npc_campaign

    def switch_pc_npc_campaign(self):
        self.campaign, self.npc_campaign = (None, self.campaign) if self.campaign_id else (self.npc_campaign, None)
        self.save()

    def get_absolute_url(self):
        return reverse("essential_characters:detail", kwargs={"slug": self.slug})

    @property
    def wound_threshold(self): return 3 + self.body
    @property
    def burden_threshold(self): return 5 + self.will // 2
    @property
    def initiative(self): return 30 + self.dexterity * 10
    @property
    def faith_level(self): return CENTURY_LEVELS[self.century][0]
    @property
    def magic_level(self): return CENTURY_LEVELS[self.century][1]
    @property
    def omen_max(self): return 2 + self.faith_level // 2
    @property
    def invocation_value(self):
        rite = self.essentialcharacterskill_set.filter(skill__name__icontains="ritus").values_list("rank", flat=True).first() or 0
        return self.faith_level + rite
    @property
    def favor_limit(self): return 1 + self.will // 2
    @property
    def arkana_max(self): return 3 + self.mind
    @property
    def favor_max(self): return 3 + self.will

    def clone(self, new_campaign=None, new_npc_campaign=None, plot=None):
        with transaction.atomic():
            clone = EssentialCharacter.objects.get(pk=self.pk)
            clone.pk = None
            clone.slug = ""
            clone.image = _copy_file(self.image)
            clone.campaign = new_campaign
            clone.npc_campaign = new_npc_campaign
            clone.plot = plot
            clone.cloned_from = self
            clone.save()
            for assignment in self.essentialcharacterskill_set.all():
                EssentialCharacterSkill.objects.create(character=clone, skill=assignment.skill, rank=assignment.rank)
            clone.magic_aspects.set(self.magic_aspects.all())
            for assignment in self.essentialcharacterweapon_set.all():
                EssentialCharacterWeapon.objects.create(character=clone, profile=assignment.profile, slot=assignment.slot)
            for assignment in self.essentialcharacterarmor_set.all():
                EssentialCharacterArmor.objects.create(character=clone, profile=assignment.profile, equipped=assignment.equipped)
            for assignment in self.essentialcharacteritem_set.all():
                EssentialCharacterItem.objects.create(character=clone, item=assignment.item, quantity=assignment.quantity)
            for assignment in self.essentialcharacterspell_set.all():
                EssentialCharacterSpell.objects.create(character=clone, profile=assignment.profile)
            return clone


class EssentialCharacterSkill(models.Model):
    character = models.ForeignKey(EssentialCharacter, on_delete=models.CASCADE)
    skill = models.ForeignKey(EssentialSkill, on_delete=models.CASCADE)
    rank = models.PositiveSmallIntegerField(default=1)
    class Meta:
        constraints = [models.UniqueConstraint(fields=("character", "skill"), name="unique_essential_character_skill")]


class EssentialWeaponProfile(models.Model):
    weapon = models.OneToOneField("armory.Weapon", on_delete=models.CASCADE)
    damage = models.CharField(max_length=40)
    range = models.CharField(max_length=80)
    grip = models.CharField(max_length=40)
    properties = models.TextField(blank=True)
    def __str__(self): return str(self.weapon)


class EssentialArmorProfile(models.Model):
    riot_gear = models.OneToOneField("armory.RiotGear", on_delete=models.CASCADE)
    protection = models.CharField(max_length=40)
    load = models.CharField(max_length=40)
    sealing = models.CharField(max_length=40)
    properties = models.TextField(blank=True)
    def __str__(self): return str(self.riot_gear)


class EssentialMagicAspectProfile(models.Model):
    spell_origin = models.OneToOneField("magic.SpellOrigin", on_delete=models.CASCADE)
    description = models.TextField(blank=True)
    def __str__(self): return str(self.spell_origin)


class EssentialSpellProfile(models.Model):
    spell = models.OneToOneField("magic.BaseSpell", on_delete=models.CASCADE)
    aspect = models.ForeignKey(EssentialMagicAspectProfile, null=True, blank=True, on_delete=models.SET_NULL)
    category = models.CharField(max_length=80, blank=True)
    element = models.CharField(max_length=80, blank=True)
    action = models.CharField(max_length=80, blank=True)
    minimum_roll = models.CharField(max_length=40, blank=True)
    cost = models.CharField(max_length=40, blank=True)
    range = models.CharField(max_length=80, blank=True)
    duration = models.CharField(max_length=80, blank=True)
    area = models.CharField(max_length=80, blank=True)
    casting_time = models.CharField(max_length=80, blank=True)
    resisted = models.CharField(max_length=40, blank=True)
    description = models.TextField(blank=True)
    def __str__(self): return str(self.spell)


class EssentialCharacterWeapon(models.Model):
    character = models.ForeignKey(EssentialCharacter, on_delete=models.CASCADE)
    profile = models.ForeignKey(EssentialWeaponProfile, on_delete=models.CASCADE)
    slot = models.CharField(max_length=20, choices=(("primary", _("Primary")), ("secondary", _("Secondary"))))


class EssentialCharacterArmor(models.Model):
    character = models.ForeignKey(EssentialCharacter, on_delete=models.CASCADE)
    profile = models.ForeignKey(EssentialArmorProfile, on_delete=models.CASCADE)
    equipped = models.BooleanField(default=True)


class EssentialCharacterItem(models.Model):
    character = models.ForeignKey(EssentialCharacter, on_delete=models.CASCADE)
    item = models.ForeignKey("armory.Item", on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)


class EssentialCharacterSpell(models.Model):
    character = models.ForeignKey(EssentialCharacter, on_delete=models.CASCADE)
    profile = models.ForeignKey(EssentialSpellProfile, on_delete=models.CASCADE)
