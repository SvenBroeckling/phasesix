import math
import random

from django.db import models
from django.db.models import Sum, Max, Q
from django.urls import reverse
from django.utils.translation import gettext_lazy as _, get_language
from sorl.thumbnail import get_thumbnail

from armory.models import Item, RiotGear, Weapon, CurrencyMapUnit, RiotGearProtection
from characters.utils import static_thumbnail
from horror.models import QuirkModifier
from magic.models import SpellTemplateModifier, SpellOrigin
from pantheon.models import PriestAction
from rules.models import Skill, Template, TemplateCategory, TemplateModifier, Extension


class CharacterQuerySet(models.QuerySet):
    def for_world_configuration(self, world_configuration):
        if world_configuration is not None:
            return self.filter(extensions=world_configuration.world.extension)
        return self.all()

    def with_templates(self):
        return self.filter(charactertemplate__id__isnull=False).distinct()


class Character(models.Model):
    objects = CharacterQuerySet.as_manager()

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

    image = models.ImageField(
        _("image"), upload_to="character_images", max_length=256, blank=True, null=True
    )
    image_copyright = models.CharField(
        _("image copyright"), max_length=40, blank=True, null=True
    )
    image_copyright_url = models.CharField(
        _("image copyright url"), max_length=150, blank=True, null=True
    )

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

    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    modified_at = models.DateTimeField(_("modified at"), auto_now=True)

    created_by = models.ForeignKey(
        "auth.User",
        verbose_name=_("created by"),
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        help_text=_("Characters without user will be cleaned daily."),
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

    reputation = models.IntegerField(_("reputation"), default=0)

    health = models.IntegerField(_("health"), default=6)
    boost = models.IntegerField(_("boost"), default=0)
    arcana = models.IntegerField(_("arcana"), default=3)
    stress = models.IntegerField(_("stress"), default=0)

    bonus_dice_used = models.IntegerField(_("Bonus dice used"), default=0)
    destiny_dice_used = models.IntegerField(_("Destiny dice used"), default=0)
    rerolls_used = models.IntegerField(_("Rerolls used"), default=0)

    latest_initiative = models.IntegerField(_("latest initiative"), default=0)

    quirks = models.ManyToManyField(
        "horror.Quirk", verbose_name=_("quirks"), blank=True
    )
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
        ordering = ("-modified_at",)

    def may_edit(self, user):
        if self.created_by == user:
            return True
        if self.pc_or_npc_campaign and self.pc_or_npc_campaign.may_edit(user):
            return True
        if not self.created_by:
            return True
        return False

    def get_absolute_url(self):
        return reverse("characters:detail", kwargs={"pk": self.id})

    def get_image_url(self, geometry="180", crop="center"):
        if self.image:
            return get_thumbnail(self.image, geometry, crop=crop, quality=99).url

        return static_thumbnail(
            f"img/silhouette.png",
            geometry_string=geometry,
            crop=crop,
        )

    def get_backdrop_image_url(self, geometry="1800", crop="center"):
        if self.backdrop_image:
            return get_thumbnail(
                self.backdrop_image, geometry, crop=crop, quality=99
            ).url
        if self.get_epoch().image:
            return get_thumbnail(
                self.get_epoch().image, geometry, crop=crop, quality=99
            ).url
        return None

    def warnings(self, world_configuration):
        """Returns game logic warnings for this character"""
        warnings = []
        if world_configuration is not None:
            if world_configuration.world.extension.select_spells_by == "o":
                if self.is_magical and not self.unlocked_spell_origins.exists():
                    warnings.append(
                        _(
                            "Your character has arcana or spell points, but you don't have any spell origins unlocked. "
                            "You will not be able to add spells. Choose an occupation with a magic origin."
                        )
                    )
        return warnings

    def get_aspect_modifier(self, aspect_name):
        m = TemplateModifier.objects.filter(
            template__charactertemplate__in=self.charactertemplate_set.all(),
            aspect=aspect_name,
        ).aggregate(Sum("aspect_modifier"))

        q = QuirkModifier.objects.filter(
            quirk__in=self.quirks.all(), aspect=aspect_name
        ).aggregate(Sum("aspect_modifier"))
        return (m["aspect_modifier__sum"] or 0) + (q["aspect_modifier__sum"] or 0)

    def get_attribute_value(self, attribute_identifier):
        return self.characterattribute_set.get(
            attribute__identifier=attribute_identifier
        ).value

    def attributes(self) -> dict:
        return {
            a.attribute.identifier: a.value for a in self.characterattribute_set.all()
        }

    def knowledge_dict(self):  # TODO: 230 Queries
        kd = {}
        for t in self.charactertemplate_set.all():
            for m in t.template.templatemodifier_set.exclude(knowledge__isnull=True):
                if m.knowledge in kd.keys():
                    kd[m.knowledge] += (
                        m.knowledge_modifier if m.knowledge_modifier is not None else 0
                    )
                else:
                    kd[m.knowledge] = m.knowledge_modifier
        return kd

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
        return TemplateModifier.objects.filter(
            template__charactertemplate__character=self, allows_priest_actions=True
        ).exists()

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

    def remove_template(self, template):
        self.charactertemplate_set.filter(template=template).delete()

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

    # Magic and Horror

    @property
    def spell_points(self):
        return self.lineage.base_spell_points + self.get_aspect_modifier(
            "base_spell_points"
        )

    @property
    def unlocked_spell_origins(self):
        return SpellOrigin.objects.filter(
            id__in=[
                t.unlocks_spell_origin.id
                for t in TemplateModifier.objects.filter(
                    unlocks_spell_origin__isnull=False,
                    template__charactertemplate__character__id=self.id,
                )
            ]
        )

    @property
    def available_stress(self):
        return self.max_stress - self.stress

    @property
    def max_stress(self):
        return self.lineage.base_max_stress + self.get_aspect_modifier(
            "base_max_stress"
        )

    @property
    def quirks_active(self):
        return self.quirks_gained - self.quirks_healed

    @property
    def quirks_need_to_be_chosen(self):
        qa = self.quirks_active - self.quirks.count()
        return qa if qa >= 0 else 0

    @property
    def max_arcana(self):
        return self.lineage.base_max_arcana + self.get_aspect_modifier(
            "base_max_arcana"
        )

    @property
    def arcana_used(self):
        return self.max_arcana - self.arcana

    @property
    def spell_points_spent(self):
        return sum([s.spell_point_cost for s in self.characterspell_set.all()])

    @property
    def spell_points_available(self):
        return self.spell_points - self.spell_points_spent

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
    def total_protection_available(self):
        """
        Returns the following structure:
        [{
          "riot_gear_protection": riot_gear_protection_object,
          "available_protection": available_protection,
        },]
        """
        rgp = RiotGearProtection.objects.filter(
            riot_gear__characterriotgear__character=self
        ).order_by("protection_type__ordering")
        res = []
        for r in rgp:
            character_riot_gear = CharacterRiotGear.objects.filter(
                character=self, riot_gear=r.riot_gear
            ).first()

            available_protection = (
                r.value
                - CharacterRiotGearProtectionUsed.objects.filter(
                    character_riot_gear=character_riot_gear,
                    protection_type=r.protection_type,
                ).aggregate(Sum("value", default=0))["value__sum"]
            )
            res.append(
                {
                    "riot_gear_protection": r,
                    "available_protection": available_protection,
                }
            )
        return res

    @property
    def total_encumbrance(self):
        return (
            self.characterriotgear_set.aggregate(Sum("riot_gear__encumbrance"))[
                "riot_gear__encumbrance__sum"
            ]
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


class CharacterAttributeQuerySet(models.QuerySet):
    def physis_attributes(self):
        return self.filter(attribute__kind="phy").order_by(
            f"attribute__name_{get_language()}"
        )

    def persona_attributes(self):
        return self.filter(attribute__kind="per").order_by(
            f"attribute__name_{get_language()}"
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


class CharacterAttribute(models.Model):
    objects = CharacterAttributeQuerySet.as_manager()
    character = models.ForeignKey(Character, models.CASCADE)
    attribute = models.ForeignKey("rules.Attribute", on_delete=models.CASCADE)

    class Meta:
        ordering = ("attribute__name_de",)

    def __str__(self):
        return "{} {}".format(self.attribute.name, self.value)

    def may_edit(self, user):
        return self.character.may_edit(user)

    @property
    def value(self):
        s = TemplateModifier.objects.filter(
            template__charactertemplate__in=self.character.charactertemplate_set.all(),
            attribute=self.attribute,
        ).aggregate(Sum("attribute_modifier"))
        q = QuirkModifier.objects.filter(
            quirk__in=self.character.quirks.all(), attribute=self.attribute
        ).aggregate(Sum("attribute_modifier"))
        return (
            1
            + (s["attribute_modifier__sum"] or 0)
            + (q["attribute_modifier__sum"] or 0)
        )


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
    def value(self):
        s = TemplateModifier.objects.filter(
            template__charactertemplate__in=self.character.charactertemplate_set.all(),
            skill=self.skill,
        ).aggregate(Sum("skill_modifier"))
        q = QuirkModifier.objects.filter(
            quirk__in=self.character.quirks.all(), skill=self.skill
        ).aggregate(Sum("skill_modifier"))
        dom = self.character.characterattribute_set.get(
            attribute=self.skill.reference_attribute_1
        ).value
        sup = self.character.characterattribute_set.get(
            attribute=self.skill.reference_attribute_2
        ).value
        attr_mod = math.ceil((dom + sup) / 2)
        return (
            attr_mod + (s["skill_modifier__sum"] or 0) + (q["skill_modifier__sum"] or 0)
        )


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

    def attack_modes_with_values(self):
        skill = self.character.characterskill_set.ranged_combat_skill()
        if self.weapon.is_hand_to_hand_weapon:
            skill = self.character.characterskill_set.hand_to_hand_combat_skill()
        if self.weapon.is_throwing_weapon:
            skill = self.character.characterskill_set.throwing_combat_skill()

        damage_potential = (
            self.modified_keywords["damage_potential"]["value"]
            if "damage_potential" in self.modified_keywords
            else 0
        )
        return [
            (am.name, skill.value + am.dice_bonus + damage_potential, am.id)
            for am in self.weapon.attack_modes.all()
        ]

    @property
    def roll_info_display(self):
        traits = [
            "{%s}: {%s}" % (k["name"], k["value"])
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
    def capacity_available(self):
        capacity = (
            self.modified_keywords["capacity"]["value"]
            if "capacity" in self.modified_keywords
            else 0
        )
        return capacity - self.capacity_used


class CharacterRiotGearQuerySet(models.QuerySet):
    def shields(self):
        return self.filter(riot_gear__type__is_shield=True)


class CharacterRiotGear(models.Model):
    objects = CharacterRiotGearQuerySet.as_manager()
    character = models.ForeignKey(Character, on_delete=models.CASCADE)
    riot_gear = models.ForeignKey("armory.RiotGear", on_delete=models.CASCADE)
    condition = models.IntegerField(_("condition"), default=100)

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
        template_value = sum(
            [
                s.spell_template.spell_point_cost
                for s in self.characterspelltemplate_set.all()
            ]
        )
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
