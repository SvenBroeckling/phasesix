import itertools
import math
import os
import random
import uuid
from decimal import Decimal, ROUND_FLOOR

from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.db import models, transaction
from django.db.models import Sum, Max, Q, Value
from django.db.models.functions import Coalesce
from django.urls import reverse
from django.utils.translation import gettext_lazy as _, get_language
from sorl.thumbnail import get_thumbnail
from transmeta import TransMeta

from armory.models import (
    Item,
    RiotGear,
    Weapon,
    CurrencyMapUnit,
    RiotGearProtection,
    RiotGearModifier,
)
from body_modifications.models import (
    BodyModificationModifier,
    BodyModificationSocketLocation,
)
from characters.utils import static_thumbnail
from horror.models import Quirk, QuirkModifier
from magic.models import SpellTemplateModifier, SpellOrigin
from pantheon.models import PriestAction
from rules.models import Skill, Template, TemplateCategory, TemplateModifier, Extension
from phasesix.models import PhaseSixModel, ModelWithImage
from worlds.unique_slugify import unique_slugify


def _copy_field_file(field_file):
    """Return a saved copy of the given FieldFile (or None if empty)."""
    if not field_file:
        return None

    field_file.open("rb")
    try:
        file_data = field_file.read()
    finally:
        field_file.close()

    base_dir, filename = os.path.split(field_file.name)
    name, ext = os.path.splitext(filename)
    new_filename = f"{name}_{uuid.uuid4().hex}{ext}"
    new_path = os.path.join(base_dir, new_filename)

    return default_storage.save(new_path, ContentFile(file_data))


class Pronoun(models.Model, metaclass=TransMeta):
    nominative = models.CharField(_("nominative"), max_length=12)
    dative = models.CharField(_("dative"), max_length=12)
    possessive = models.CharField(_("possessive"), max_length=12)
    copula_verb = models.CharField(_("copula verb"), max_length=12)

    class Meta:
        translate = ("nominative", "dative", "possessive", "copula_verb")

    def __str__(self):
        return f"{self.nominative}/{self.dative}"


class Contact(models.Model):
    character = models.ForeignKey("characters.Character", on_delete=models.CASCADE)
    name = models.CharField(_("name"), max_length=80)
    occupation = models.ForeignKey(
        "rules.Template",
        limit_choices_to={"category__name_en": "Occupation"},
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    description = models.TextField(_("description"), blank=True, null=True)

    class Meta:
        ordering = ("name",)
        verbose_name = _("Contact")
        verbose_name_plural = _("Contacts")


class CharacterQuerySet(models.QuerySet):
    def for_world(self, world):
        if world is not None:
            return self.filter(extensions=world.extension)
        return self.all()

    def with_templates(self):
        return self.filter(charactertemplate__id__isnull=False).distinct()

    def npc(self):
        return self.filter(npc_campaign__isnull=False)

    def pc(self):
        return self.filter(npc_campaign__isnull=True)


class Character(ModelWithImage, PhaseSixModel):
    objects = CharacterQuerySet.as_manager()
    image_upload_to = "character_images"

    slug = models.SlugField(_("slug"), max_length=220)
    name = models.CharField(_("name"), max_length=80)
    description = models.TextField(_("description"), blank=True, null=True)

    may_appear_on_start_page = models.BooleanField(
        _("may appear on start page"),
        help_text=_(
            "This character may appear on the anonymous start page (i.E. if it has only free images"
        ),
        default=False,
    )

    size = models.IntegerField(_("size"), blank=True, null=True)
    weight = models.IntegerField(_("weight"), blank=True, null=True)
    date_of_birth = models.CharField(
        _("date of birth"), max_length=40, blank=True, null=True
    )
    entity = models.ForeignKey(
        "pantheon.Entity",
        verbose_name=_("entity"),
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )
    attitude = models.IntegerField(_("attitude"), default=50)
    grace = models.IntegerField(_("grace"), default=0)

    backdrop_image = models.ImageField(
        _("backdrop image"),
        upload_to="character_backdrop_images",
        max_length=256,
        blank=True,
        null=True,
    )
    backdrop_copyright = models.CharField(
        _("image copyright"), max_length=40, blank=True, null=True
    )
    backdrop_copyright_url = models.CharField(
        _("image copyright url"), max_length=150, blank=True, null=True
    )

    pronoun = models.ForeignKey(
        Pronoun,
        verbose_name=_("pronoun"),
        on_delete=models.CASCADE,
    )

    created_by = models.ForeignKey(
        "auth.User",
        verbose_name=_("created by"),
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        help_text=_("Characters without user will be cleaned daily."),
    )
    is_favorite = models.BooleanField(
        _("is favorite"),
        default=False,
    )

    cloned_from = models.ForeignKey(
        "self",
        verbose_name=_("cloned from"),
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="clones",
    )

    extensions = models.ManyToManyField(
        "rules.Extension", limit_choices_to={"is_mandatory": False}
    )

    lineage = models.ForeignKey(
        "rules.Lineage", verbose_name=_("lineage"), on_delete=models.CASCADE
    )

    currency_map = models.ForeignKey(
        "armory.CurrencyMap", verbose_name=_("currency map"), on_delete=models.CASCADE
    )

    campaign = models.ForeignKey(
        "campaigns.Campaign",
        verbose_name=_("Campaign"),
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )
    npc_campaign = models.ForeignKey(
        "campaigns.Campaign",
        verbose_name=_("NPC Campaign"),
        related_name="npc_set",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )
    plot = models.ForeignKey(
        "plots.Plot",
        verbose_name=_("Plot Campaign"),
        related_name="plot_npc_set",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )

    reputation = models.IntegerField(_("reputation"), default=0)

    health = models.IntegerField(_("health"), default=6)
    boost = models.IntegerField(_("boost"), default=0)
    arcana = models.IntegerField(_("arcana"), default=3)
    base_stress = models.IntegerField(_("base stress"), default=0)
    stress = models.IntegerField(_("stress"), default=0)

    bonus_dice_used = models.IntegerField(_("Bonus dice used"), default=0)
    destiny_dice_used = models.IntegerField(_("Destiny dice used"), default=0)
    rerolls_used = models.IntegerField(_("Rerolls used"), default=0)

    latest_initiative = models.IntegerField(_("latest initiative"), default=0)

    # Horror
    quirks_gained = models.IntegerField(
        _("quirks gained"),
        default=0,
        help_text=_("The amount of quirks gained by excess stress"),
    )
    quirks_healed = models.IntegerField(
        _("quirks healed"),
        default=0,
        help_text=_("The amount of quirks healed by treatment."),
    )

    def __str__(self):
        return self.name

    class Meta:
        ordering = (
            "-is_favorite",
            "-created_at",
        )

    def save(self, **kwargs):
        if not self.slug:
            unique_slugify(self, str(self.name))
        super().save(**kwargs)

    def may_edit(self, user):
        if self.created_by == user:
            return True
        if self.pc_or_npc_campaign and self.pc_or_npc_campaign.may_edit(user):
            return True
        if not self.created_by:
            return True
        return False

    def get_absolute_url(self):
        return reverse("characters:detail", kwargs={"slug": self.slug})

    def get_image_url(self, geometry="180", crop="center"):
        if self.image:
            return get_thumbnail(self.image, geometry, crop=crop, quality=99).url

        return static_thumbnail(
            f"img/silhouette.png",
            geometry_string=geometry,
            crop=crop,
        )

    def get_backdrop_image_url(self, geometry="1800x500", crop="center"):
        if self.backdrop_image:
            return get_thumbnail(
                self.backdrop_image, geometry, crop=crop, quality=99
            ).url
        if self.get_epoch().image:
            return get_thumbnail(
                self.get_epoch().image, geometry, crop=crop, quality=99
            ).url
        return None

    def clone(self, new_campaign=None, new_npc_campaign=None, plot=None):
        with transaction.atomic():
            clone = Character(
                name=self.name,
                description=self.description,
                may_appear_on_start_page=self.may_appear_on_start_page,
                size=self.size,
                weight=self.weight,
                date_of_birth=self.date_of_birth,
                entity=self.entity,
                attitude=self.attitude,
                grace=self.grace,
                image=_copy_field_file(self.image),
                image_copyright=self.image_copyright,
                image_copyright_url=self.image_copyright_url,
                backdrop_image=_copy_field_file(self.backdrop_image),
                backdrop_copyright=self.backdrop_copyright,
                backdrop_copyright_url=self.backdrop_copyright_url,
                pronoun=self.pronoun,
                created_by=self.created_by,
                is_favorite=self.is_favorite,
                lineage=self.lineage,
                currency_map=self.currency_map,
                campaign=new_campaign,
                npc_campaign=new_npc_campaign,
                plot=plot,
                reputation=self.reputation,
                health=self.health,
                boost=self.boost,
                arcana=self.arcana,
                base_stress=self.base_stress,
                stress=self.stress,
                bonus_dice_used=self.bonus_dice_used,
                destiny_dice_used=self.destiny_dice_used,
                rerolls_used=self.rerolls_used,
                latest_initiative=self.latest_initiative,
                quirks_gained=self.quirks_gained,
                quirks_healed=self.quirks_healed,
                cloned_from=self,
            )

            # Ensure a fresh slug is generated
            clone.pk = None
            clone.slug = None
            clone.save()

            clone.extensions.set(self.extensions.all())

            for attr in self.characterattribute_set.all():
                CharacterAttribute.objects.create(
                    character=clone,
                    attribute=attr.attribute,
                    modifier=attr.modifier,
                )

            for skill in self.characterskill_set.all():
                CharacterSkill.objects.create(character=clone, skill=skill.skill)

            for status_effect in self.characterstatuseffect_set.all():
                CharacterStatusEffect.objects.create(
                    character=clone,
                    status_effect=status_effect.status_effect,
                    base_value=status_effect.base_value,
                )

            for template in self.charactertemplate_set.all():
                CharacterTemplate.objects.create(
                    character=clone, template=template.template
                )

            for bm in self.characterbodymodification_set.all():
                CharacterBodyModification.objects.create(
                    character=clone,
                    body_modification=bm.body_modification,
                    socket_location=bm.socket_location,
                    is_active=bm.is_active,
                    socket_amount=bm.socket_amount,
                    charges_used=bm.charges_used,
                )

            riot_gear_map = {}
            for rg in self.characterriotgear_set.all():
                new_rg = CharacterRiotGear.objects.create(
                    character=clone,
                    riot_gear=rg.riot_gear,
                    condition=rg.condition,
                    is_equipped=rg.is_equipped,
                )
                riot_gear_map[rg.id] = new_rg

            for used in CharacterRiotGearProtectionUsed.objects.filter(
                character_riot_gear__character=self
            ):
                new_rg = riot_gear_map.get(used.character_riot_gear_id)
                if new_rg:
                    CharacterRiotGearProtectionUsed.objects.create(
                        character_riot_gear=new_rg,
                        protection_type=used.protection_type,
                        value=used.value,
                    )

            for weapon in self.characterweapon_set.all():
                new_weapon = CharacterWeapon.objects.create(
                    character=clone,
                    weapon=weapon.weapon,
                    condition=weapon.condition,
                    capacity_used=weapon.capacity_used,
                )
                new_weapon.modifications.set(weapon.modifications.all())

            item_map = {}
            for item in self.characteritem_set.all():
                new_item = CharacterItem.objects.create(
                    character=clone,
                    quantity=item.quantity,
                    charges_used=item.charges_used,
                    item=item.item,
                    ordering=item.ordering,
                )
                item_map[item.id] = new_item

            for item in self.characteritem_set.exclude(in_container__isnull=True):
                new_item = item_map.get(item.id)
                container = item_map.get(item.in_container_id)
                if new_item and container:
                    new_item.in_container = container
                    new_item.save(update_fields=["in_container"])

            for spell in self.characterspell_set.all():
                new_spell = CharacterSpell.objects.create(
                    character=clone,
                    spell=spell.spell,
                    custom_name=spell.custom_name,
                )
                for template in spell.characterspelltemplate_set.all():
                    CharacterSpellTemplate.objects.create(
                        character_spell=new_spell,
                        spell_template=template.spell_template,
                    )

            for currency in self.charactercurrency_set.all():
                CharacterCurrency.objects.create(
                    character=clone,
                    currency_map_unit=currency.currency_map_unit,
                    quantity=currency.quantity,
                )

            for note in self.characternote_set.all():
                CharacterNote.objects.create(
                    character=clone,
                    is_private=note.is_private,
                    subject=note.subject,
                    text=note.text,
                    ordering=note.ordering,
                )

            for foe in self.characterfoe_set.all():
                CharacterFoe.objects.create(
                    character=clone,
                    foe=foe.foe,
                    health=foe.health,
                    max_health=foe.max_health,
                    boost=foe.boost,
                    name=foe.name,
                    is_familiar=foe.is_familiar,
                    image=_copy_field_file(foe.image),
                )

            for recipe in self.characterrecipe_set.all():
                CharacterRecipe.objects.create(character=clone, recipe=recipe.recipe)

            for quirk in self.characterquirk_set.all():
                CharacterQuirk.objects.create(character=clone, quirk=quirk.quirk)

            for lang in self.characterlanguage_set.all():
                CharacterLanguage.objects.create(
                    character=clone,
                    language=lang.language,
                    modifier=lang.modifier,
                )

            for contact in self.contact_set.all():
                Contact.objects.create(
                    character=clone,
                    name=contact.name,
                    occupation=contact.occupation,
                    description=contact.description,
                )

            return clone

    def warnings(self, world):
        """Returns game logic warnings for this character"""
        warnings = []
        if self.is_magical and not self.unlocked_spell_origins.exists():
            warnings.append(
                _(
                    "Your character has arcana or spell points, but you don't have any spell origins unlocked. "
                    "You will not be able to add spells. Choose an occupation with a magic origin."
                )
            )
        return warnings

    def _load_all_aspect_modifiers(self):
        """Load all aspect modifiers at once to prevent N+1 queries"""
        if not hasattr(self, "_aspect_modifiers_cache"):
            template_modifiers = (
                TemplateModifier.objects.for_character(self)
                .values("aspect")
                .annotate(total=Sum("aspect_modifier"))
            )
            riotgear_modifiers = (
                RiotGearModifier.objects.for_character(self)
                .values("aspect")
                .annotate(total=Sum("aspect_modifier"))
            )
            quirk_modifiers = (
                QuirkModifier.objects.for_character(self)
                .values("aspect")
                .annotate(total=Sum("aspect_modifier"))
            )
            body_modifiers = (
                BodyModificationModifier.objects.for_character(self)
                .values("aspect")
                .annotate(total=Sum("aspect_modifier"))
            )

            self._aspect_modifiers_cache = {}

            for modifier_list in [
                template_modifiers,
                riotgear_modifiers,
                quirk_modifiers,
                body_modifiers,
            ]:
                for item in modifier_list:
                    aspect = item["aspect"]
                    value = item["total"] or 0
                    if aspect not in self._aspect_modifiers_cache:
                        self._aspect_modifiers_cache[aspect] = 0
                    self._aspect_modifiers_cache[aspect] += value

        return self._aspect_modifiers_cache

    def get_aspect_modifier(self, aspect_name):
        """Get the combined aspect modifier value with caching to reduce queries"""
        modifiers = self._load_all_aspect_modifiers()
        return modifiers.get(aspect_name, 0)

    def get_attribute_value(self, attribute_identifier):
        return self.characterattribute_set.get(
            attribute__identifier=attribute_identifier
        ).value

    def attributes(self) -> dict:
        return {
            a.attribute.identifier: a.value
            for a in self.characterattribute_set.prefetch_related("attribute")
        }

    def _load_knowledge_dict(self):
        kd = {}
        knowledge_modifiers = TemplateModifier.objects.filter(
            template__charactertemplate__character=self, knowledge__isnull=False
        ).annotate(total=Sum("knowledge_modifier"))

        for km in knowledge_modifiers:
            kd[km.knowledge] = km.total or 0

        return kd

    def knowledge_dict(self):
        """Return a dict of knowledge modifiers"""
        if not hasattr(self, "_knowledge_dict"):
            self._knowledge_dict_cache = self._load_knowledge_dict()
        return self._knowledge_dict_cache

    def switch_pc_npc_campaign(self):
        if self.campaign is not None:
            self.npc_campaign = self.campaign
            self.campaign = None
        else:
            self.campaign = self.npc_campaign
            self.npc_campaign = None
        self.save()

    @property
    def pc_or_npc_campaign(self):
        return self.campaign or self.npc_campaign

    @property
    def ws_room_name(self) -> str:
        """Websocket room name"""
        if self.pc_or_npc_campaign is not None:
            return self.pc_or_npc_campaign.ws_room_name
        return f"character-{self.id}"

    @property
    def priest_actions(self):
        return PriestAction.objects.all()

    @property
    def is_priest(self):
        return any(
            [
                TemplateModifier.objects.for_character(self).allows_priest_actions(),
                RiotGearModifier.objects.for_character(self).allows_priest_actions(),
                QuirkModifier.objects.for_character(self).allows_priest_actions(),
                BodyModificationModifier.objects.for_character(
                    self
                ).allows_priest_actions(),
            ]
        )

    @property
    def is_magical(self):
        return self.max_arcana > 0 or self.spell_points > 0

    @property
    def skills(self):
        return self.characterskill_set.for_extensions(self.extensions)

    def currency_quantity(self, currency_map_unit):
        qs = self.charactercurrency_set.filter(currency_map_unit=currency_map_unit)
        return qs.latest("id").quantity if qs.exists() else 0

    @property
    def common_currency_unit(self):
        return CurrencyMapUnit.objects.filter(
            currency_map__character__id=self.id, is_common=True
        ).latest("id")

    def subtract_currency(self, amount):
        """
        Subtract a given amount (in common currency units) from the character's currencies.
        - If the common unit is insufficient, break larger units into the common unit
          according to CurrencyMapUnit.value until enough common currency is available,
          or no more higher units remain.
        - Returns True if the subtraction succeeded, False otherwise. Persists changes.
        """

        amount = Decimal(str(amount)).quantize(Decimal("0.01"))
        if amount <= 0:
            return True

        units = list(
            CurrencyMapUnit.objects.filter(currency_map=self.currency_map).order_by(
                "-value"
            )
        )
        if not units:
            return False

        qty_by_unit = {}
        for u in units:
            cc = (
                self.charactercurrency_set.filter(currency_map_unit=u).latest("id")
                if self.charactercurrency_set.filter(currency_map_unit=u).exists()
                else None
            )
            qty_by_unit[u.id] = cc.quantity if cc else 0

        common_unit = next((u for u in units if u.is_common), None)
        if common_unit is None:
            return False

        def current_common_qty_decimal():
            total = Decimal("0.00")
            for u in units:
                q = qty_by_unit.get(u.id, 0)
                if q:
                    total += Decimal(q) * Decimal(u.value)
            return total

        common_available = current_common_qty_decimal()
        if common_available < amount:
            for u in units:
                if u.id == common_unit.id:
                    continue
                while qty_by_unit.get(u.id, 0) > 0 and common_available < amount:
                    qty_by_unit[u.id] -= 1
                    common_available += Decimal(u.value)

        if common_available < amount:
            return False

        original_common_qty = (
            self.charactercurrency_set.filter(currency_map_unit=common_unit)
            .latest("id")
            .quantity
            if self.charactercurrency_set.filter(currency_map_unit=common_unit).exists()
            else 0
        )

        for u in units:
            if u.id == common_unit.id:
                continue
            new_q = qty_by_unit.get(u.id, 0)
            qs = self.charactercurrency_set.filter(currency_map_unit=u)
            if qs.exists():
                obj = qs.latest("id")
                if obj.quantity != new_q:
                    obj.quantity = new_q
                    obj.save()
            else:
                if new_q > 0:
                    self.charactercurrency_set.create(
                        currency_map_unit=u, quantity=new_q
                    )

        common_unit_value = Decimal(common_unit.value)
        desired_common_units_total = (common_available / common_unit_value).quantize(
            Decimal("1"), rounding=ROUND_FLOOR
        )
        units_to_subtract = (amount / common_unit_value).quantize(
            Decimal("1"), rounding=ROUND_FLOOR
        )

        if (amount % common_unit_value) != 0:
            units_to_subtract += 1
        if units_to_subtract > desired_common_units_total:
            return False
        remaining_common_units = int(desired_common_units_total - units_to_subtract)

        qs_common = self.charactercurrency_set.filter(currency_map_unit=common_unit)
        if qs_common.exists():
            obj = qs_common.latest("id")
            obj.quantity = remaining_common_units
            obj.save()
        else:
            self.charactercurrency_set.create(
                currency_map_unit=common_unit, quantity=remaining_common_units
            )
        return True

    @property
    def templates_with_rules(self):
        return self.charactertemplate_set.exclude(
            template__rules_de__isnull=True
        ).exclude(template__rules_de="")

    @property
    def templates_with_combat_rules(self):
        return self.charactertemplate_set.filter(template__show_rules_in_combat=True)

    def add_template(self, template):
        if not self.charactertemplate_set.filter(template=template).exists():
            self.charactertemplate_set.create(template=template)
            self.clear_aspect_modifiers_cache()

    def remove_template(self, template):
        self.charactertemplate_set.filter(template=template).delete()
        self.clear_aspect_modifiers_cache()

    def clear_aspect_modifiers_cache(self):
        """Clear the aspect modifiers cache to force recalculation"""
        if hasattr(self, "_aspect_modifiers_cache"):
            del self._aspect_modifiers_cache
        if hasattr(self, "_attribute_modifiers_cache"):
            del self._attribute_modifiers_cache

    def get_epoch(self) -> Extension:
        return self.extensions.filter(is_mandatory=False, type="e").earliest("id")

    @property
    def world(self):
        try:
            return self.extensions.filter(is_mandatory=False, type="w").earliest("id")
        except Extension.DoesNotExist:
            return None

    @property
    def extension_enabled(self):
        res = {}
        for e in self.extensions.all():
            res[e.identifier] = True
        return res

    # Reputation

    @property
    def reputation_spent(self):
        ts = self.charactertemplate_set.aggregate(Sum("template__cost"))
        tc = ts["template__cost__sum"] if ts is not None else 0
        return tc or 0

    @property
    def reputation_available(self):
        return self.reputation - self.reputation_spent

    @property
    def reputation_gained(self):
        campaign_points = (
            self.pc_or_npc_campaign.starting_template_points
            if self.pc_or_npc_campaign
            else 0
        )
        return self.reputation - self.lineage.template_points - campaign_points

    def set_initial_reputation(self, initial_reputation=None):
        self.reputation = (
            self.reputation_spent if initial_reputation is None else initial_reputation
        )
        self.save()

    @property
    def remaining_template_points(self):
        spent_points = (
            self.charactertemplate_set.aggregate(Sum("template__cost"))[
                "template__cost__sum"
            ]
            or 0
        )
        campaign_points = (
            self.pc_or_npc_campaign.starting_template_points
            if self.pc_or_npc_campaign
            else 0
        )
        return self.lineage.template_points + campaign_points - spent_points

    # Languages and Contacts
    @property
    def max_languages(self):
        base = self.lineage.base_languages + self.get_aspect_modifier("base_languages")
        return (
            base
            + self.get_attribute_value("education")
            + self.get_attribute_value("logic")
        )

    @property
    def max_contacts(self):
        base = self.lineage.base_contacts + self.get_aspect_modifier("base_contacts")
        return (
            base
            + self.get_attribute_value("charm")
            + self.get_attribute_value("attractiveness")
        )

    # Horror
    @property
    def calculated_base_stress(self):
        """
        This is worded differently from other base_ aspects.
        The reason is, that the aspect itself is named base,
        and it can be modified by the player *and* by templates etc.
        """
        return self.base_stress + self.get_aspect_modifier("base_base_stress")

    @property
    def available_stress(self):
        return self.max_stress - max(self.stress, self.calculated_base_stress)

    @property
    def max_stress(self):
        return self.lineage.base_max_stress + self.get_aspect_modifier(
            "base_max_stress"
        )

    @property
    def quirks(self):
        return Quirk.objects.filter(characterquirk__character=self)

    def add_quirk(self, quirk):
        CharacterQuirk.objects.get_or_create(character=self, quirk=quirk)

    def remove_quirk(self, quirk):
        CharacterQuirk.objects.filter(character=self, quirk=quirk).delete()

    @property
    def quirks_active(self):
        return self.quirks_gained - self.quirks_healed

    @property
    def quirks_need_to_be_chosen(self):
        qa = self.quirks_active - self.quirks.count()
        return qa if qa >= 0 else 0

    @property
    def is_consumed_by_dread(self):
        return self.stress >= self.max_stress

    # Magic
    @property
    def spell_points(self):
        return self.lineage.base_spell_points + self.get_aspect_modifier(
            "base_spell_points"
        )

    @property
    def spell_points_spent(self):
        base_cost = self.characterspell_set.aggregate(
            total=Coalesce(Sum("spell__spell_point_cost"), Value(0))
        )
        template_cost = self.characterspell_set.annotate(
            template_sum=Coalesce(
                Sum("characterspelltemplate__spell_template__spell_point_cost"),
                Value(0),
            )
        ).aggregate(total=Coalesce(Sum("template_sum"), Value(0)))
        return base_cost["total"] + template_cost["total"]

    @property
    def spell_points_available(self):
        return self.spell_points - self.spell_points_spent

    @property
    def unlocked_spell_origins(self):
        t = TemplateModifier.objects.for_character(self).unlocked_spell_origins()
        r = RiotGearModifier.objects.for_character(self).unlocked_spell_origins()
        q = QuirkModifier.objects.for_character(self).unlocked_spell_origins()
        b = BodyModificationModifier.objects.for_character(
            self
        ).unlocked_spell_origins()
        return SpellOrigin.objects.filter(id__in=itertools.chain(t, r, q, b))

    @property
    def max_arcana(self):
        return self.lineage.base_max_arcana + self.get_aspect_modifier(
            "base_max_arcana"
        )

    @property
    def arcana_used(self):
        return self.max_arcana - self.arcana

    # Body Modifications

    @property
    def bio_strain(self):
        bm_sum = (
            CharacterBodyModification.objects.filter(
                character=self, body_modification__bio_strain__isnull=False
            ).aggregate(Sum("body_modification__bio_strain"))[
                "body_modification__bio_strain__sum"
            ]
            or 0
        )
        return (
            self.lineage.base_bio_strain
            + self.get_aspect_modifier("base_bio_strain")
            + bm_sum
        )

    @property
    def energy_produced(self):
        bm_sum = (
            CharacterBodyModification.objects.filter(
                character=self,
                is_active=True,
                body_modification__energy_consumption_ma__isnull=False,
                body_modification__energy_consumption_ma__lt=0,
            ).aggregate(Sum("body_modification__energy_consumption_ma"))[
                "body_modification__energy_consumption_ma__sum"
            ]
            or 0
        )
        return (
            self.lineage.base_energy
            + self.get_aspect_modifier("base_energy")
            + abs(bm_sum)
        )

    @property
    def energy_consumed(self):
        bm_sum = (
            CharacterBodyModification.objects.filter(
                character=self,
                is_active=True,
                body_modification__energy_consumption_ma__isnull=False,
                body_modification__energy_consumption_ma__gt=0,
            ).aggregate(Sum("body_modification__energy_consumption_ma"))[
                "body_modification__energy_consumption_ma__sum"
            ]
            or 0
        )
        return abs(bm_sum)

    def sockets(self, location_identifier):
        bm_sum = (
            CharacterBodyModification.objects.filter(
                character=self, socket_location__identifier=location_identifier
            ).aggregate(Sum("socket_amount"))["socket_amount__sum"]
            or 0
        )
        return (
            getattr(self.lineage, f"base_sockets_{location_identifier}")
            + self.get_aspect_modifier(f"base_sockets_{location_identifier}")
            - bm_sum
        )

    @property
    def sockets_head(self):
        return self.sockets("head")

    @property
    def sockets_torso(self):
        return self.sockets("torso")

    @property
    def sockets_left_arm(self):
        return self.sockets("left_arm")

    @property
    def sockets_right_arm(self):
        return self.sockets("right_arm")

    @property
    def sockets_left_leg(self):
        return self.sockets("left_leg")

    @property
    def sockets_right_leg(self):
        return self.sockets("right_leg")

    # Dice and Rolls

    @property
    def minimum_roll(self):
        return self.lineage.base_minimum_roll + self.get_aspect_modifier(
            "base_minimum_roll"
        )

    @property
    def bonus_dice(self):
        return self.lineage.base_bonus_dice + self.get_aspect_modifier(
            "base_bonus_dice"
        )

    @property
    def destiny_dice(self):
        return self.lineage.base_destiny_dice + self.get_aspect_modifier(
            "base_destiny_dice"
        )

    @property
    def rerolls(self):
        return self.lineage.base_rerolls + self.get_aspect_modifier("base_rerolls")

    @property
    def bonus_dice_free(self):
        return self.bonus_dice - self.bonus_dice_used

    @property
    def destiny_dice_free(self):
        return self.destiny_dice - self.destiny_dice_used

    @property
    def rerolls_free(self):
        return self.rerolls - self.rerolls_used

    @property
    def stress_test_dice(self):
        return self.get_attribute_value("willpower") + self.get_attribute_value("logic")

    # Combat

    @property
    def actions(self):
        return self.lineage.base_actions + self.get_aspect_modifier("base_actions")

    @property
    def combat_walking_range(self):
        return self.get_attribute_value("quickness") + 1

    @property
    def combat_running_range(self):
        return self.get_attribute_value("quickness") + 5

    @property
    def combat_crawling_range(self):
        return int(math.ceil(self.get_attribute_value("quickness") / 2)) + 1

    @property
    def base_protection(self):
        return self.lineage.base_protection + self.get_aspect_modifier(
            "base_protection"
        )

    @property
    def total_protection_available(self):
        """
        Returns the following structure:
        [{
          "riot_gear_protection": riot_gear_protection_object,
          "available_protection": available_protection,
          "used_protection": used_protection,
        },]
        Only considers equipped riot gear.
        """
        rgp = RiotGearProtection.objects.filter(
            riot_gear__characterriotgear__character=self,
            riot_gear__characterriotgear__is_equipped=True,
        ).order_by("protection_type__ordering")
        res = []
        for r in rgp:
            character_riot_gear = CharacterRiotGear.objects.filter(
                character=self, riot_gear=r.riot_gear, is_equipped=True
            ).first()

            used_protection = CharacterRiotGearProtectionUsed.objects.filter(
                character_riot_gear=character_riot_gear,
                protection_type=r.protection_type,
            ).aggregate(Sum("value", default=0))["value__sum"]

            available_protection = r.value - used_protection

            if available_protection or used_protection:
                res.append(
                    {
                        "riot_gear_protection": r,
                        "available_protection": available_protection,
                        "used_protection": used_protection,
                    }
                )
        return res

    @property
    def total_encumbrance(self):
        return (
            self.characterriotgear_set.filter(is_equipped=True).aggregate(
                Sum("riot_gear__encumbrance")
            )["riot_gear__encumbrance__sum"]
            or 0
        )

    @property
    def evasion(self):
        character_evasion = int(
            math.ceil(
                (
                    self.get_attribute_value("deftness")
                    + self.get_attribute_value("quickness")
                )
                / 2
            )
        )
        mods = self.get_aspect_modifier("base_evasion")
        return (
            character_evasion
            + self.lineage.base_evasion
            + mods
            - self.total_encumbrance
        )

    @property
    def rest_wound_dice(self):
        return (
            self.get_attribute_value("resistance")
            + self.get_attribute_value("endurance")
            + self.get_attribute_value("willpower")
        )

    @property
    def rest_arcana_dice(self):
        return (
            self.get_attribute_value("charm")
            + self.get_attribute_value("conscientiousness")
            + self.get_attribute_value("willpower")
        )

    @property
    def rest_stress_dice(self):
        return self.get_attribute_value("willpower") + self.get_attribute_value("logic")

    @property
    def weaponless_attack_dice(self):
        bonus = 1 if self.get_attribute_value("quickness") > 2 else 0
        return self.characterskill_set.hand_to_hand_combat_skill().value + bonus

    @property
    def weaponless_piercing(self):
        return 1 if self.get_attribute_value("strength") > 2 else 0

    @property
    def max_health(self):
        return self.lineage.base_max_health + self.get_aspect_modifier(
            "base_max_health"
        )

    @property
    def wounds_taken(self):
        return self.max_health - self.health

    @property
    def max_concealment(self):
        ic = (
            self.characteritem_set.aggregate(Max("item__concealment"))[
                "item__concealment__max"
            ]
            or 0
        )
        rc = (
            self.characterriotgear_set.aggregate(Max("riot_gear__concealment"))[
                "riot_gear__concealment__max"
            ]
            or 0
        )
        wc = 0
        for w in self.characterweapon_set.all():
            if "concealment" in w.modified_keywords:
                wc = max(wc, w.modified_keywords["concealment"]["value"])
        return max(ic, rc, wc)

    def randomize(self, reputation):
        while reputation > 0:
            template = (
                Template.objects.for_extensions(self.extensions).order_by("?").first()
            )
            self.charactertemplate_set.create(template=template)
            reputation -= template.cost
        for i in range(2):
            self.characterriotgear_set.create(
                riot_gear=RiotGear.objects.for_extensions(self.extensions)
                .order_by("?")
                .first()
            )
        for i in range(3):
            self.characterweapon_set.create(
                weapon=Weapon.objects.for_extensions(self.extensions)
                .order_by("?")
                .first()
            )
        for i in range(12):
            self.characteritem_set.create(
                item=Item.objects.for_extensions(self.extensions).order_by("?").first(),
                quantity=random.randint(1, 3),
            )


class CharacterSkillQuerySet(models.QuerySet):
    def for_extensions(self, extension_rm):
        return self.filter(
            Q(skill__extensions__id__in=extension_rm.all())
            | Q(skill__extensions__id__in=Extension.objects.filter(is_mandatory=True))
        )

    def mind_skills(self):
        return self.filter(skill__kind="m").order_by(f"skill__name_{get_language()}")

    def practical_skills(self):
        return self.filter(skill__kind="p").order_by(f"skill__name_{get_language()}")

    def ranged_combat_skill(self):
        return self.get(skill__name_en="Shooting")

    def hand_to_hand_combat_skill(self):
        return self.get(skill__name_en="Hand to Hand Combat")

    def throwing_combat_skill(self):
        return self.get(skill__name_en="Throwing")

    def evasion_skill(self):
        return self.get(skill__name_en="Acrobatics")

    def spell_casting_skill(self):
        return self.get(skill__name_en="Spell Casting")


class CharacterLanguage(models.Model):
    character = models.ForeignKey(Character, models.CASCADE)
    language = models.ForeignKey("worlds.Language", on_delete=models.CASCADE)
    modifier = models.IntegerField(_("Modifier"), default=0)


class CharacterQuirk(models.Model):
    character = models.ForeignKey(Character, on_delete=models.CASCADE)
    quirk = models.ForeignKey("horror.Quirk", on_delete=models.CASCADE)
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)

    class Meta:
        ordering = ("quirk__id",)
        unique_together = ("character", "quirk")

    def __str__(self):
        return f"{self.character} - {self.quirk}"

    def may_edit(self, user):
        return self.character.may_edit(user)


class CharacterAttributeQuerySet(models.QuerySet):
    def physis_attributes(self):
        return (
            self.filter(attribute__kind="phy")
            .order_by(f"attribute__name_{get_language()}")
            .prefetch_related("attribute")
        )

    def persona_attributes(self):
        return (
            self.filter(attribute__kind="per")
            .order_by(f"attribute__name_{get_language()}")
            .prefetch_related("attribute")
        )


class CharacterAttribute(models.Model):
    objects = CharacterAttributeQuerySet.as_manager()
    character = models.ForeignKey(Character, models.CASCADE)
    attribute = models.ForeignKey("rules.Attribute", on_delete=models.CASCADE)
    modifier = models.IntegerField(_("Modifier"), default=0)

    class Meta:
        ordering = ("attribute__name_de",)

    def __str__(self):
        return "{} {}".format(self.attribute.name, self.value)

    def may_edit(self, user):
        return self.character.may_edit(user)

    @property
    def base_value(self):
        if not hasattr(self.character, "_attribute_modifiers_cache"):
            self._load_attribute_modifiers()

        attribute_id = self.attribute.identifier
        return 1 + self.character._attribute_modifiers_cache.get(attribute_id, 0)

    def _load_attribute_modifiers(self):
        """Load all attribute modifiers at once to prevent N+1 queries"""
        character = self.character
        if not hasattr(character, "_attribute_modifiers_cache"):
            template_modifiers = (
                TemplateModifier.objects.for_character(character)
                .values("attribute__identifier")
                .annotate(total=Sum("attribute_modifier"))
            )
            riotgear_modifiers = (
                RiotGearModifier.objects.for_character(character)
                .values("attribute__identifier")
                .annotate(total=Sum("attribute_modifier"))
            )
            quirk_modifiers = (
                QuirkModifier.objects.for_character(character)
                .values("attribute__identifier")
                .annotate(total=Sum("attribute_modifier"))
            )
            body_modifiers = (
                BodyModificationModifier.objects.for_character(character)
                .values("attribute__identifier")
                .annotate(total=Sum("attribute_modifier"))
            )

            character._attribute_modifiers_cache = {}

            for modifier_list in [
                template_modifiers,
                riotgear_modifiers,
                quirk_modifiers,
                body_modifiers,
            ]:
                for item in modifier_list:
                    attribute_id = item["attribute__identifier"]
                    if attribute_id is not None:  # Skip None values
                        value = item["total"] or 0
                        if attribute_id not in character._attribute_modifiers_cache:
                            character._attribute_modifiers_cache[attribute_id] = 0
                        character._attribute_modifiers_cache[attribute_id] += value

    @property
    def value(self):
        return self.base_value + self.modifier


class CharacterSkill(models.Model):
    objects = CharacterSkillQuerySet.as_manager()

    character = models.ForeignKey(Character, models.CASCADE)
    skill = models.ForeignKey("rules.Skill", models.CASCADE)

    class Meta:
        ordering = ("skill__name_de",)

    def __str__(self):
        return "{} {}".format(self.skill.name, self.value)

    def may_edit(self, user):
        return self.character.may_edit(user)

    @property
    def base_value(self):
        s = TemplateModifier.objects.for_character(self.character).skill_modifier_sum(
            self.skill
        )
        r = RiotGearModifier.objects.for_character(self.character).skill_modifier_sum(
            self.skill
        )
        q = QuirkModifier.objects.for_character(self.character).skill_modifier_sum(
            self.skill
        )
        b = BodyModificationModifier.objects.for_character(
            self.character
        ).skill_modifier_sum(self.skill)
        return s + r + q + b

    @property
    def modifier(self):
        return self.character.characterattribute_set.get(
            attribute=self.skill.reference_attribute_1
        ).value

    @property
    def value(self):
        return self.base_value + self.modifier


class CharacterStatusEffect(models.Model):
    character = models.ForeignKey(Character, models.CASCADE)
    status_effect = models.ForeignKey("rules.StatusEffect", models.CASCADE)
    base_value = models.IntegerField(_("base value"), default=0)

    class Meta:
        ordering = ("status_effect__ordering",)

    def __str__(self):
        return self.status_effect.name

    @property
    def value(self):
        return self.base_value


class CharacterTemplate(models.Model):
    character = models.ForeignKey(Character, models.CASCADE)
    template = models.ForeignKey("rules.Template", models.CASCADE)
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)

    class Meta:
        ordering = ("template__category__sort_order",)

    def __str__(self):
        return self.template.name

    def may_edit(self, user):
        return self.character.may_edit(user)


class CharacterBodyModificationQuerySet(models.QuerySet):
    def head(self):
        return self.filter(socket_location__identifier="head")

    def torso(self):
        return self.filter(socket_location__identifier="torso")

    def right_arm(self):
        return self.filter(socket_location__identifier="right_arm")

    def left_arm(self):
        return self.filter(socket_location__identifier="left_arm")

    def right_leg(self):
        return self.filter(socket_location__identifier="right_leg")

    def left_leg(self):
        return self.filter(socket_location__identifier="left_leg")

    def usable_in_combat(self):
        return self.filter(body_modification__usable_in_combat=True)


class CharacterBodyModification(models.Model):
    objects = CharacterBodyModificationQuerySet.as_manager()
    character = models.ForeignKey(Character, models.CASCADE)
    body_modification = models.ForeignKey(
        "body_modifications.BodyModification", models.CASCADE
    )
    socket_location = models.ForeignKey(
        "body_modifications.SocketLocation", models.CASCADE
    )
    is_active = models.BooleanField(_("is active"), default=True)
    socket_amount = models.IntegerField(_("socket amount"), default=1)
    charges_used = models.IntegerField(_("charges used"), default=0)
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)

    class Meta:
        ordering = ("body_modification__rarity",)

    def __str__(self):
        return self.body_modification.name

    def may_edit(self, user):
        return self.character.may_edit(user)

    @property
    def charges_left(self):
        try:
            return self.body_modification.charges - self.charges_used
        except TypeError:
            return None


class CharacterWeapon(models.Model):
    character = models.ForeignKey(Character, on_delete=models.CASCADE)
    weapon = models.ForeignKey("armory.Weapon", on_delete=models.CASCADE)
    modifications = models.ManyToManyField("armory.WeaponModification")
    condition = models.IntegerField(default=100)
    capacity_used = models.IntegerField(_("capacity used"), default=0)

    class Meta:
        ordering = ("weapon__id",)

    def may_edit(self, user):
        return self.character.may_edit(user)

    def value_for_attack_mode(self, attack_mode):
        skill = self.character.characterskill_set.ranged_combat_skill()
        if self.weapon.is_hand_to_hand_weapon:
            skill = self.character.characterskill_set.hand_to_hand_combat_skill()
        if self.weapon.is_throwing_weapon:
            skill = self.character.characterskill_set.throwing_combat_skill()
        return skill.value + attack_mode.dice_bonus + self.damage_potential

    @property
    def roll_info_display(self):
        traits = [
            "{}: {}".format(k["name"], k["value"])
            for k in self.modified_keywords.values()
            if k["show_in_dice_rolls"]
        ]

        for template in self.character.charactertemplate_set.filter(
            template__show_in_attack_dice_rolls=True
        ):
            traits.append(template.template.name)
        if traits:
            return f"({', '.join(traits)})"
        return ""

    @property
    def has_modifications_with_rules(self):
        return self.modifications.filter(
            Q(rules_de__isnull=False) | Q(rules_en__isnull=False)
        ).exists()

    @property
    def modified_keywords(self):
        """
        Returns a dict with all keywords, their description and their values for this weapon
        - All keywords from the weapon
        - All keywords from the modifications WeaponModificationKeyword.value
        - If a keyword is modified by a modification, the value is the sum of the base value and the modification value
        - If a keyword is present in the modification, but not in the weapon, it is added to the dict
        """
        weapon_keywords = {
            k.keyword.identifier: {
                "name": k.keyword.name,
                "description": k.keyword.description,
                "value": k.value,
                "is_rare": k.keyword.is_rare,
                "show_in_dice_rolls": k.keyword.show_in_dice_rolls,
                "show_in_summary": k.keyword.show_in_summary,
            }
            for k in self.weapon.weaponkeyword_set.order_by("-keyword__ordering")
        }
        for mod in self.modifications.all():
            for k in mod.weaponmodificationkeyword_set.all():
                if k.keyword.identifier in weapon_keywords:
                    weapon_keywords[k.keyword.identifier]["value"] += k.value
                else:
                    weapon_keywords[k.keyword.identifier] = {
                        "name": k.keyword.name,
                        "description": k.keyword.description,
                        "value": k.value,
                        "is_rare": k.keyword.is_rare,
                        "show_in_dice_rolls": k.keyword.show_in_dice_rolls,
                        "show_in_summary": k.keyword.show_in_summary,
                    }
        return weapon_keywords

    @property
    def damage_potential(self):
        return (
            self.modified_keywords["damage_potential"]["value"]
            if "damage_potential" in self.modified_keywords
            else 0
        )

    @property
    def capacity(self):
        return (
            self.modified_keywords["capacity"]["value"]
            if "capacity" in self.modified_keywords
            else 0
        )

    @property
    def capacity_available(self):
        return self.capacity - self.capacity_used


class CharacterRiotGearQuerySet(models.QuerySet):
    def shields(self):
        return self.filter(riot_gear__type__is_shield=True)


class CharacterRiotGear(models.Model):
    objects = CharacterRiotGearQuerySet.as_manager()
    character = models.ForeignKey(Character, on_delete=models.CASCADE)
    riot_gear = models.ForeignKey("armory.RiotGear", on_delete=models.CASCADE)
    condition = models.IntegerField(_("condition"), default=100)
    is_equipped = models.BooleanField(_("is equipped"), default=True)

    def may_edit(self, user):
        return self.character.may_edit(user)

    class Meta:
        ordering = ("riot_gear__id",)


class CharacterRiotGearProtectionUsed(models.Model):
    character_riot_gear = models.ForeignKey(CharacterRiotGear, on_delete=models.CASCADE)
    protection_type = models.ForeignKey(
        "armory.ProtectionType", on_delete=models.CASCADE
    )
    value = models.IntegerField(_("value"), default=0)

    class Meta:
        ordering = ("character_riot_gear__id",)


class CharacterItemQuerySet(models.QuerySet):
    def usable_in_combat(self):
        return self.filter(item__usable_in_combat=True)

    def without_containers(self):
        return self.filter(item__is_container=False)

    def containers(self):
        return self.filter(item__is_container=True)

    def not_in_container(self):
        return self.filter(in_container__isnull=True)


class CharacterItem(models.Model):
    objects = CharacterItemQuerySet.as_manager()

    character = models.ForeignKey(Character, on_delete=models.CASCADE)
    quantity = models.IntegerField(_("Quantity"), default=1)
    charges_used = models.IntegerField(_("Charges used"), default=0)
    item = models.ForeignKey("armory.Item", on_delete=models.CASCADE)
    in_container = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, blank=True
    )
    ordering = models.IntegerField(_("Ordering"), default=1)

    class Meta:
        ordering = ("ordering",)

    def may_edit(self, user):
        return self.character.may_edit(user)

    @property
    def charges_available(self):
        if self.item.charges is not None:
            return self.item.charges - self.charges_used
        return None

    @property
    def other_containers(self):
        return self.character.characteritem_set.containers().exclude(
            id=self.in_container_id
        )


class CharacterSpell(models.Model):
    character = models.ForeignKey(Character, on_delete=models.CASCADE)
    spell = models.ForeignKey("magic.BaseSpell", on_delete=models.CASCADE)
    custom_name = models.CharField(
        _("custom name"), max_length=30, null=True, blank=True
    )

    class Meta:
        ordering = ("spell__id",)

    def __str__(self):
        return self.spell.name

    def may_edit(self, user):
        return self.character.may_edit(user)

    @property
    def dice_value(self):
        attribute = self.spell_type.reference_attribute
        try:
            da = self.character.characterattribute_set.get(attribute=attribute).value
        except CharacterAttribute.DoesNotExist:
            da = 0

        try:
            sc = self.character.characterskill_set.spell_casting_skill().value
        except CharacterSkill.DoesNotExist:
            sc = 0

        return da + sc

    def modifier_attribute_modification(self, attribute_name):
        mod = 0
        for t in self.characterspelltemplate_set.all():
            for m in t.spell_template.spelltemplatemodifier_set.filter(
                attribute=attribute_name
            ):
                mod += m.attribute_modifier
        return mod

    @property
    def name(self):
        return self.custom_name if self.custom_name else self.spell.name

    @property
    def spell_type(self):
        for t in self.characterspelltemplate_set.all():
            for m in t.spell_template.spelltemplatemodifier_set.filter(
                type_change__isnull=False
            ):
                return m.type_change
        return self.spell.type

    @property
    def variant(self):
        for t in self.characterspelltemplate_set.all():
            for m in t.spell_template.spelltemplatemodifier_set.filter(
                variant_change__isnull=False
            ):
                return m.variant_change
        return self.spell.variant

    @property
    def power(self):
        return 1 + self.modifier_attribute_modification("power")

    @property
    def needs_concentration(self):
        return self.spell.needs_concentration

    @property
    def duration(self):
        return self.spell.duration

    @property
    def duration_unit(self):
        return self.spell.duration_unit

    @property
    def get_duration_unit_display(self):
        return self.spell.get_duration_unit_display()

    @property
    def range(self):
        return self.spell.range + self.modifier_attribute_modification("range")

    @property
    def shape(self):
        for t in self.characterspelltemplate_set.all():
            for m in t.spell_template.spelltemplatemodifier_set.filter(
                shape_change__isnull=False
            ):
                return m.shape_change
        return self.spell.shape

    @property
    def actions(self):
        return self.spell.actions + self.modifier_attribute_modification("actions")

    @property
    def is_ritual(self):
        return self.spell.is_ritual

    @property
    def arcana_cost(self):
        return self.spell.arcana_cost + self.modifier_attribute_modification(
            "arcana_cost"
        )

    @property
    def spell_point_cost(self):
        from django.db.models import Sum, Value
        from django.db.models.functions import Coalesce

        # Prefetch template costs in a single query
        template_value = self.characterspelltemplate_set.aggregate(
            total=Coalesce(Sum("spell_template__spell_point_cost"), Value(0))
        )["total"]

        return template_value + self.spell.spell_point_cost


class CharacterSpellTemplate(models.Model):
    character_spell = models.ForeignKey(CharacterSpell, on_delete=models.CASCADE)
    spell_template = models.ForeignKey("magic.SpellTemplate", on_delete=models.CASCADE)

    def __str__(self):
        return self.spell_template.name


class CharacterCurrency(models.Model):
    character = models.ForeignKey(Character, on_delete=models.CASCADE)
    currency_map_unit = models.ForeignKey(
        "armory.CurrencyMapUnit", on_delete=models.CASCADE
    )
    quantity = models.IntegerField(_("quantity"), default=0)


class CharacterNote(models.Model):
    objects = CharacterItemQuerySet.as_manager()

    character = models.ForeignKey(Character, on_delete=models.CASCADE)
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    is_private = models.BooleanField(_("is private"), default=False)
    subject = models.CharField(_("subject"), max_length=80, null=True, blank=True)
    text = models.TextField(_("text"))
    ordering = models.IntegerField(_("ordering"), default=1)

    class Meta:
        ordering = "ordering", "created_at"

    def may_edit(self, user):
        return self.character.may_edit(user)


class CharacterFoe(models.Model):
    character = models.ForeignKey(Character, on_delete=models.CASCADE)
    foe = models.ForeignKey("rules.Foe", on_delete=models.CASCADE)
    health = models.IntegerField(_("health"), default=0)
    max_health = models.IntegerField(_("max health"), default=0)
    boost = models.IntegerField(_("boost"), default=0)
    name = models.CharField(_("name"), max_length=30, null=True, blank=True)
    is_familiar = models.BooleanField(_("is familiar"), default=False)
    image = models.ImageField(
        _("image"),
        upload_to="character_foe_images",
        max_length=256,
        blank=True,
        null=True,
    )

    class Meta:
        ordering = ("name", "foe__name_de")
        verbose_name = _("character foe")
        verbose_name_plural = _("character foes")

    def __str__(self):
        return self.name or self.foe.name

    def may_edit(self, user):
        return self.character.may_edit(user)

    def get_image_url(self, geometry="180", crop="center"):
        # Prefer custom image if available; otherwise fall back to the base Foe image
        if self.image:
            return get_thumbnail(self.image, geometry, crop=crop, quality=99).url
        return self.foe.get_image_url(geometry, crop)

    @property
    def wounds_taken(self):
        return self.max_health - self.health


class CharacterRecipe(models.Model):
    character = models.ForeignKey(Character, on_delete=models.CASCADE)
    recipe = models.ForeignKey("potions.Recipe", on_delete=models.CASCADE)

    class Meta:
        ordering = ("recipe__name_de",)
        verbose_name = _("Recipe")
        verbose_name_plural = _("Recipes")

    def __str__(self):
        return self.recipe.name

    def may_edit(self, user):
        return self.character.may_edit(user)
