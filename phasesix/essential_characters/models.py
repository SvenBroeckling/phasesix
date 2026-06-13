import os
import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.db import models, transaction
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from sorl.thumbnail import get_thumbnail
from transmeta import TransMeta

from phasesix.models import ModelWithImage, image_upload_path
from worlds.unique_slugify import unique_slugify
from .rules import (
    ATTRIBUTES,
    CENTURY_LEVELS,
    magic_slots,
    valid_attribute_distribution,
    valid_skill_distribution,
)


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
    return default_storage.save(
        os.path.join(root, f"{stem}_{uuid.uuid4().hex}{extension}"), ContentFile(data)
    )


class EssentialBond(models.Model, metaclass=TransMeta):
    name = models.CharField(_("name"), max_length=160, unique=True)
    description = models.CharField(_("description"), max_length=500, blank=True)
    benefit = models.CharField(_("benefit"), max_length=255, blank=True)
    vulnerability = models.CharField(_("vulnerability"), max_length=255, blank=True)

    class Meta:
        ordering = ("name_de",)
        translate = ("name", "description", "benefit", "vulnerability")

    def __str__(self):
        return self.name


class EssentialCharacterQuerySet(models.QuerySet):
    def pc(self):
        return self.filter(npc_campaign__isnull=True)

    def npc(self):
        return self.filter(npc_campaign__isnull=False)

    def for_world(self, world):
        return (
            self.filter(
                models.Q(campaign__world_extension=world.extension)
                | models.Q(npc_campaign__world_extension=world.extension)
            ).distinct()
            if world
            else self
        )


class EssentialCharacter(ModelWithImage):
    objects = EssentialCharacterQuerySet.as_manager()
    image_upload_to = "essential_character_images"
    slug = models.SlugField(_("slug"), max_length=220, unique=True)
    name = models.CharField(_("name"), max_length=80)
    birth_date = models.CharField(_("birth date"), max_length=40, blank=True)
    century = models.PositiveSmallIntegerField(_("century"), default=1)
    concept = models.CharField(_("concept"), max_length=500, blank=True)
    oath_or_debt = models.TextField(_("oath or debt"), blank=True)
    notes = models.TextField(_("notes"), blank=True)
    image = models.ImageField(
        _("image"),
        upload_to=image_upload_path,
        max_length=256,
        blank=True,
        null=True,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("created by"),
        on_delete=models.CASCADE,
    )
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    modified_at = models.DateTimeField(_("modified at"), auto_now=True)
    is_favorite = models.BooleanField(_("is favorite"), default=False)
    cloned_from = models.ForeignKey(
        "self",
        verbose_name=_("cloned from"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="clones",
    )
    campaign = models.ForeignKey(
        "campaigns.Campaign",
        verbose_name=_("campaign"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    npc_campaign = models.ForeignKey(
        "campaigns.Campaign",
        verbose_name=_("NPC campaign"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="essential_npc_set",
    )
    plot = models.ForeignKey(
        "plots.Plot",
        verbose_name=_("plot"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="essential_plot_npc_set",
    )
    ancestry = models.ForeignKey(
        "rules.Lineage",
        verbose_name=_("ancestry"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    path = models.ForeignKey(
        "rules.Template",
        verbose_name=_("path"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    bond = models.ForeignKey(
        EssentialBond,
        verbose_name=_("bond"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    mind = models.PositiveSmallIntegerField(_("mind"), default=0)
    will = models.PositiveSmallIntegerField(_("will"), default=0)
    instinct = models.PositiveSmallIntegerField(_("instinct"), default=0)
    dexterity = models.PositiveSmallIntegerField(_("dexterity"), default=0)
    body = models.PositiveSmallIntegerField(_("body"), default=0)
    presence = models.PositiveSmallIntegerField(_("presence"), default=0)
    gift = models.PositiveSmallIntegerField(_("gift"), default=0)
    perception = models.PositiveSmallIntegerField(_("perception"), default=0)
    wounds = models.PositiveSmallIntegerField(_("wounds"), default=0)
    burden = models.PositiveSmallIntegerField(_("burden"), default=0)
    omen = models.PositiveSmallIntegerField(_("omen"), default=0)
    arkana = models.PositiveSmallIntegerField(_("arkana"), default=0)
    favor = models.PositiveSmallIntegerField(_("favor"), default=0)
    corruption = models.PositiveSmallIntegerField(_("corruption"), default=0)
    focus = models.CharField(_("focus"), max_length=200, blank=True)
    regeneration_ritual = models.TextField(_("regeneration ritual"), blank=True)
    magic_aspects = models.ManyToManyField(
        "magic.SpellOrigin", verbose_name=_("magic aspects"), blank=True
    )
    spells = models.ManyToManyField(
        "magic.BaseSpell", verbose_name=_("spells"), blank=True
    )
    items = models.ManyToManyField("armory.Item", verbose_name=_("items"), blank=True)
    weapons = models.ManyToManyField(
        "armory.Weapon", verbose_name=_("weapons"), blank=True
    )
    armor = models.ManyToManyField(
        "armory.RiotGear", verbose_name=_("armor"), blank=True
    )

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
            raise ValidationError(
                _("Attributes must use the Essential starting distribution.")
            )
        for field in ("ancestry", "path", "bond"):
            if not getattr(self, f"{field}_id"):
                raise ValidationError({field: _("Select a mark.")})
        if self.campaign_id and self.npc_campaign_id:
            raise ValidationError(
                _("A character cannot be both a PC and NPC in a campaign.")
            )
        if (
            self.plot_id
            and (self.campaign_id or self.npc_campaign_id)
            and self.plot.campaign_id != (self.campaign_id or self.npc_campaign_id)
        ):
            raise ValidationError(
                _("Character plot and campaign assignments must match.")
            )
        for campaign in filter(None, (self.campaign, self.npc_campaign)):
            if (
                campaign.ruleset != "tirakan_essential"
                or campaign.world_extension.identifier != "tirakan"
            ):
                raise ValidationError(
                    _("Essential characters may only join Tirakan Essential campaigns.")
                )
        if self.plot_id and (
            self.plot.ruleset != "tirakan_essential"
            or self.plot.world_extension.identifier != "tirakan"
        ):
            raise ValidationError(
                _("Essential characters may only join Tirakan Essential plots.")
            )

    def save(self, *args, **kwargs):
        if not self.slug:
            unique_slugify(self, self.name)
        self.full_clean()
        return super().save(*args, **kwargs)

    def validate_assignments(self):
        ranks = list(self.essentialcharacterskill_set.values_list("rank", flat=True))
        if ranks and not valid_skill_distribution(ranks):
            raise ValidationError(
                _(
                    "Skills must contain one rank 3, three rank 2, and all remaining skills at rank 1."
                )
            )
        slots = magic_slots(self.gift)
        if (
            self.magic_aspects.count() > slots["aspects"]
            or self.spells.count() > slots["spells"]
        ):
            raise ValidationError(
                _("The supernatural selections exceed the slots granted by Gift.")
            )

    def may_edit(self, user):
        return self.created_by == user or bool(
            self.pc_or_npc_campaign and self.pc_or_npc_campaign.may_edit(user)
        )

    @property
    def pc_or_npc_campaign(self):
        return self.campaign or self.npc_campaign

    def switch_pc_npc_campaign(self):
        self.campaign, self.npc_campaign = (
            (None, self.campaign) if self.campaign_id else (self.npc_campaign, None)
        )
        self.save()

    def get_absolute_url(self):
        return reverse("essential_characters:detail", kwargs={"slug": self.slug})

    def get_image_url(self, geometry="180", crop="center"):
        if self.image:
            return get_thumbnail(self.image, geometry, crop=crop, quality=99).url
        return None

    @property
    def wound_threshold(self):
        return 3 + self.body

    @property
    def burden_threshold(self):
        return 5 + self.will // 2

    @property
    def initiative(self):
        return 30 + self.dexterity * 10

    @property
    def faith_level(self):
        return CENTURY_LEVELS[self.century][0]

    @property
    def magic_level(self):
        return CENTURY_LEVELS[self.century][1]

    @property
    def omen_max(self):
        return 2 + self.faith_level // 2

    @property
    def invocation_value(self):
        rite = (
            self.essentialcharacterskill_set.filter(name__icontains="ritus")
            .values_list("rank", flat=True)
            .first()
            or 0
        )
        return self.faith_level + rite

    @property
    def favor_limit(self):
        return 1 + self.will // 2

    @property
    def arkana_max(self):
        return 3 + self.mind

    @property
    def favor_max(self):
        return 3 + self.will

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
                EssentialCharacterSkill.objects.create(
                    character=clone, name=assignment.name, rank=assignment.rank
                )
            clone.magic_aspects.set(self.magic_aspects.all())
            clone.spells.set(self.spells.all())
            clone.items.set(self.items.all())
            clone.weapons.set(self.weapons.all())
            clone.armor.set(self.armor.all())
            return clone


class EssentialCharacterSkill(models.Model):
    character = models.ForeignKey(
        EssentialCharacter, verbose_name=_("character"), on_delete=models.CASCADE
    )
    name = models.CharField(_("name"), max_length=160)
    rank = models.PositiveSmallIntegerField(_("rank"), default=1)

    class Meta:
        ordering = ("name",)
        constraints = [
            models.UniqueConstraint(
                fields=("character", "name"), name="unique_essential_character_skill"
            )
        ]

    def __str__(self):
        return self.name
