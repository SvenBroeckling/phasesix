import itertools

from django.conf import settings
from django.contrib import admin
from django.db import models
from django.db.models import Q, Sum
from django.utils.translation import gettext_lazy as _
from sorl.thumbnail import get_thumbnail
from transmeta import TransMeta, get_real_fieldname

from armory.choices import COLOR_CLASS_CHOICES
from armory.mixins import SearchableCardListMixin
from characters.utils import static_thumbnail
from homebrew.models import HomebrewModel, HomebrewQuerySet
from phasesix.models import ModelWithImage, PhaseSixModel
from worlds.models import World
from worlds.unique_slugify import unique_slugify

CHARACTER_ASPECT_CHOICES = (
    ("base_languages", _("languages")),
    ("base_contacts", _("contacts")),
    ("base_max_health", _("max health")),
    ("base_max_arcana", _("max arcana")),
    ("base_spell_points", _("spell points")),
    ("base_actions", _("actions")),
    ("base_minimum_roll", _("minimum roll")),
    ("base_rest_minimum_roll", _("rest minimum roll")),
    ("base_protection", _("protection")),
    ("base_evasion", _("evasion")),
    ("base_bonus_dice", _("bonus dice")),
    ("base_destiny_dice", _("destiny dice")),
    ("base_rerolls", _("rerolls")),
    ("base_base_stress", _("base stress")),
    ("base_max_stress", _("max stress")),
)


class ModifierBaseQuerySet(models.QuerySet):
    def for_character(self, character):
        if hasattr(self.model, "template"):
            return self.filter(
                template__charactertemplate__in=character.charactertemplate_set.all(),
            )
        if hasattr(self.model, "riot_gear"):
            return self.filter(
                riot_gear__characterriotgear__in=character.characterriotgear_set.all()
            )
        if hasattr(self.model, "quirk"):
            return self.filter(quirk__in=character.quirks.all())
        if hasattr(self.model, "body_modification"):
            return self.filter(
                body_modification__in=character.characterbodymodification_set.filter(
                    is_active=True
                ).values_list("body_modification", flat=True)
            )
        return self.none()

    def skill_modifier_sum(self, skill):
        return (
            self.filter(skill=skill).aggregate(Sum("skill_modifier"))[
                "skill_modifier__sum"
            ]
            or 0
        )

    def aspect_modifier_sum(self, aspect):
        return (
            self.filter(aspect=aspect).aggregate(Sum("aspect_modifier"))[
                "aspect_modifier__sum"
            ]
            or 0
        )

    def attribute_modifier_sum(self, attribute_identifier):
        return (
            self.filter(attribute__identifier=attribute_identifier).aggregate(
                Sum("attribute_modifier")
            )["attribute_modifier__sum"]
            or 0
        )

    def allows_priest_actions(self):
        return self.filter(allows_priest_actions=True).exists()

    def unlocked_spell_origins(self):
        return (
            self.filter(unlocks_spell_origin__isnull=False)
            .distinct()
            .values_list("unlocks_spell_origin__id", flat=True)
        )


def modifiers_for_qs(qs):
    """
    Returns a dictionary with the modifiers for an object with modifiers (Template,
    BodyModification, RiotGear, Quirk, etc.). Aggregates the modifiers for each
    aspect, attribute, skill, knowledge, and spell origin.
    """
    mods = {}

    aspect_totals = {}
    attribute_totals = {}
    skill_totals = {}
    knowledge_totals = {}
    spell_origin_names = set()

    aspect_label_map = dict(CHARACTER_ASPECT_CHOICES)
    iter_qs = qs.select_related(
        "attribute",
        "skill",
        "knowledge",
        "unlocks_spell_origin",
    )

    for row in iter_qs:
        if row.aspect is not None and row.aspect_modifier is not None:
            aspect_totals[row.aspect] = (
                aspect_totals.get(row.aspect, 0) + row.aspect_modifier
            )
        if row.attribute_id is not None and row.attribute_modifier is not None:
            name = row.attribute.name  # translatable field via TransMeta
            attribute_totals[name] = (
                attribute_totals.get(name, 0) + row.attribute_modifier
            )
        if row.skill_id is not None and row.skill_modifier is not None:
            name = row.skill.name
            skill_totals[name] = skill_totals.get(name, 0) + row.skill_modifier
        if row.knowledge_id is not None and row.knowledge_modifier is not None:
            name = row.knowledge.name
            knowledge_totals[name] = (
                knowledge_totals.get(name, 0) + row.knowledge_modifier
            )
        if row.unlocks_spell_origin_id is not None:
            spell_origin_names.add(row.unlocks_spell_origin.name)

    if aspect_totals:
        aspects = {}
        for code, total in aspect_totals.items():
            if total:
                label = str(aspect_label_map.get(code, code))
                aspects[label] = f"+{total}" if total > 0 else f"{total}"
        if aspects:
            mods["aspects"] = aspects
    if attribute_totals:
        attributes = {
            str(name): f"+{total}" if total > 0 else f"{total}"
            for name, total in attribute_totals.items()
            if total
        }
        if attributes:
            mods["attributes"] = attributes
    if skill_totals:
        skills = {
            str(name): f"+{total}" if total > 0 else f"{total}"
            for name, total in skill_totals.items()
            if total
        }
        if skills:
            mods["skills"] = skills
    if knowledge_totals:
        knowledge = {
            str(name): f"+{total}" if total > 0 else f"{total}"
            for name, total in knowledge_totals.items()
            if total
        }
        if knowledge:
            mods["knowledge"] = knowledge
    if spell_origin_names:
        mods["spell_origins"] = {str(name): True for name in sorted(spell_origin_names)}

    return mods


class ModifierBase(models.Model, metaclass=TransMeta):
    objects = ModifierBaseQuerySet.as_manager()

    aspect = models.CharField(
        verbose_name=_("aspect"),
        max_length=40,
        choices=CHARACTER_ASPECT_CHOICES,
        null=True,
        blank=True,
    )
    aspect_modifier = models.IntegerField(
        verbose_name=_("aspect modifier"), blank=True, null=True
    )
    attribute = models.ForeignKey(
        "rules.Attribute",
        on_delete=models.CASCADE,
        verbose_name=_("attribute"),
        null=True,
        blank=True,
    )
    attribute_modifier = models.IntegerField(
        verbose_name=_("attribute modifier"), blank=True, null=True
    )
    skill = models.ForeignKey(
        "rules.Skill",
        on_delete=models.CASCADE,
        verbose_name=_("skill"),
        null=True,
        blank=True,
    )
    skill_modifier = models.IntegerField(
        verbose_name=_("skill modifier"), blank=True, null=True
    )
    knowledge = models.ForeignKey(
        "rules.Knowledge",
        on_delete=models.CASCADE,
        verbose_name=_("knowledge"),
        null=True,
        blank=True,
    )
    knowledge_modifier = models.IntegerField(
        verbose_name=_("knowledge modifier"), blank=True, null=True
    )
    unlocks_spell_origin = models.ForeignKey(
        "magic.SpellOrigin",
        verbose_name=_("unlocks spell origin"),
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )
    allows_priest_actions = models.BooleanField(
        _("allows priest actions"), default=False
    )

    class Meta:
        abstract = True


class ExtensionSelectQuerySet(models.QuerySet):
    def for_extensions(self, extension_rm):
        if isinstance(extension_rm, Extension):
            extension_rm = Extension.objects.filter(pk=extension_rm.pk)
        return self.filter(
            Q(extensions__id__in=extension_rm.all())
            | Q(extensions__id__in=Extension.objects.filter(is_mandatory=True))
        )

    def for_world(self, world):
        core = Extension.objects.filter(is_mandatory=True)
        return self.filter(
            extensions__in=itertools.chain(
                [world.extension, world.extension.fixed_epoch],
                core,
                world.extension.fixed_extensions.all(),
            )
        )


class ExtensionQuerySet(models.QuerySet):
    def active(self):
        return self.filter(is_active=True)

    def for_world_identifier(self, world_identifier):
        world = World.objects.get(extension__identifier=world_identifier)
        return self.for_world(world)

    def for_world(self, world):
        if world is None:
            return self.active()

        q = Q(is_mandatory=True)
        if world and world.extension:
            q |= Q(pk=world.extension.pk)
            q |= Q(pk__in=world.extension.fixed_extensions.all())
        if world and world.extension.fixed_epoch:
            q |= Q(pk=world.extension.fixed_epoch.pk)
        return self.active().filter(q)

    def first_class_extensions(self):
        return self.filter(Q(type="e") | Q(is_mandatory=True)).filter(is_active=True)


class Extension(ModelWithImage, PhaseSixModel, metaclass=TransMeta):
    """
    A PhaseSix source book extension
    """

    EXTENSION_TYPE_CHOICES = (
        ("x", _("Extension")),
        ("e", _("Epoch")),
        ("w", _("World")),
    )
    objects = ExtensionQuerySet.as_manager()
    image_upload_to = "extension_images"

    is_mandatory = models.BooleanField(_("is mandatory"), default=False)
    is_active = models.BooleanField(_("is active"), default=True)
    type = models.CharField(
        _("type"), max_length=1, choices=EXTENSION_TYPE_CHOICES, default="x"
    )

    name = models.CharField(_("name"), max_length=120)
    identifier = models.CharField(_("identifier"), max_length=20)
    description = models.TextField(_("description"), blank=True, null=True)
    image_prompt_prefix = models.TextField(
        _("image prompt prefix"),
        blank=True,
        default="",
        help_text=_("Optional prompt text prepended to AI image generation."),
    )

    year_range = models.CharField(_("year range"), blank=True, null=True, max_length=50)
    fa_icon_class = models.CharField(
        _("FA Icon Class"), max_length=30, default="fas fa-book"
    )
    fa_icon_latex = models.CharField(_("FA Icon LaTeX"), max_length=30, default="")

    ordering = models.IntegerField(_("ordering"), default=100)

    # only world related
    currency_map = models.ForeignKey(
        "armory.CurrencyMap", blank=True, null=True, on_delete=models.SET_NULL
    )
    fixed_extensions = models.ManyToManyField(
        "self",
        blank=True,
        limit_choices_to={"type": "x"},
        help_text=_(
            "Mandatory extensions for a world. Only applies if this object is a world"
        ),
    )
    fixed_epoch = models.ForeignKey(
        "self",
        limit_choices_to={"type": "e"},
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )
    exclusive_languages = models.BooleanField(
        default=False, help_text=_("Don't allow epoch languages if this is set.")
    )

    class Meta:
        ordering = ("ordering",)
        translate = ("name", "description", "year_range")
        verbose_name = _("extension")
        verbose_name_plural = _("extensions")

    @property
    def is_epoch(self):
        return self.type == "e"

    @property
    def is_world(self):
        return self.type == "w"

    def __str__(self):
        return self.name


class Lineage(PhaseSixModel, metaclass=TransMeta):
    objects = ExtensionSelectQuerySet.as_manager()

    name = models.CharField(_("name"), max_length=80)
    description = models.TextField(_("description"), blank=True, null=True)

    extensions = models.ManyToManyField("rules.Extension")
    template = models.ForeignKey(
        "rules.Template", blank=True, null=True, on_delete=models.SET_NULL
    )

    base_languages = models.IntegerField(_("languages"), default=0)
    base_contacts = models.IntegerField(_("contacts"), default=0)

    base_max_health = models.IntegerField(_("max health"), default=6)

    base_max_arcana = models.IntegerField(_("max arcana"), default=0)
    base_spell_points = models.IntegerField(_("spell points"), default=0)

    base_actions = models.IntegerField(_("base actions"), default=2)
    base_minimum_roll = models.IntegerField(_("base minimum roll"), default=5)

    base_bonus_dice = models.IntegerField(_("base bonus dice"), default=0)
    base_destiny_dice = models.IntegerField(_("base destiny dice"), default=0)
    base_rerolls = models.IntegerField(_("base rerolls"), default=0)

    # Base Values
    base_evasion = models.IntegerField(_("base evasion"), default=0)
    base_protection = models.IntegerField(_("base armor"), default=0)

    # horror
    base_base_stress = models.IntegerField(_("max stress"), default=0)  # Yes, base_base
    base_max_stress = models.IntegerField(_("max stress"), default=10)
    template_points = models.IntegerField(_("template points"), default=20)

    # Body Modifications
    base_bio_strain = models.IntegerField(_("bio strain"), default=0)
    base_energy = models.IntegerField(_("energy"), default=0)
    base_sockets_head = models.IntegerField(_("sockets head"), default=1)
    base_sockets_torso = models.IntegerField(_("sockets torso"), default=4)
    base_sockets_left_arm = models.IntegerField(_("sockets left arm"), default=2)
    base_sockets_right_arm = models.IntegerField(_("sockets right arm"), default=2)
    base_sockets_left_leg = models.IntegerField(_("sockets left leg"), default=2)
    base_sockets_right_leg = models.IntegerField(_("sockets right leg"), default=2)

    class Meta:
        translate = ("name", "description")
        verbose_name = _("lineage")
        verbose_name_plural = _("lineages")

    def __str__(self):
        return self.name


class Attribute(models.Model, metaclass=TransMeta):
    KIND_CHOICES = (
        ("per", _("persona")),
        ("phy", _("physis")),
    )
    name = models.CharField(_("name"), max_length=120)
    identifier = models.CharField(_("identifier"), max_length=120)
    description = models.TextField(_("description"), blank=True, null=True)
    kind = models.CharField(_("kind"), max_length=3, choices=KIND_CHOICES)

    class Meta:
        translate = ("name", "description")
        verbose_name = _("attribute")
        verbose_name_plural = _("attributes")

    def __str__(self):
        return self.name


class Skill(models.Model, metaclass=TransMeta):
    objects = ExtensionSelectQuerySet.as_manager()
    KIND_CHOICES = (
        ("p", _("practical")),
        ("m", _("mind")),
    )
    name = models.CharField(_("name"), max_length=120)
    description = models.TextField(_("description"), blank=True, null=True)
    kind = models.CharField(_("kind"), max_length=1, choices=KIND_CHOICES)
    extensions = models.ManyToManyField("rules.Extension")
    is_magical = models.BooleanField(_("is magical"), default=False)

    reference_attribute_1 = models.ForeignKey(
        "rules.Attribute",
        verbose_name=_("reference attribute 1"),
        related_name="reference_attribute_1_set",
        on_delete=models.CASCADE,
    )
    reference_attribute_2 = models.ForeignKey(
        "rules.Attribute",
        verbose_name=_("reference attribute 2"),
        related_name="reference_attribute_2_set",
        on_delete=models.CASCADE,
    )

    class Meta:
        translate = ("name", "description")
        verbose_name = _("skill")
        verbose_name_plural = _("skills")

    def __str__(self):
        return self.name


class Knowledge(PhaseSixModel, metaclass=TransMeta):
    objects = ExtensionSelectQuerySet.as_manager()

    name = models.CharField(_("name"), max_length=120)
    extensions = models.ManyToManyField("rules.Extension")
    description = models.TextField(_("description"), blank=True, null=True)
    skill = models.ForeignKey(
        Skill, verbose_name=_("Skill"), blank=True, null=True, on_delete=models.SET_NULL
    )

    class Meta:
        translate = ("name", "description")
        verbose_name = _("knowledge")
        verbose_name_plural = _("knowledge")

    def __str__(self):
        return self.name


class TemplateCategory(SearchableCardListMixin, models.Model, metaclass=TransMeta):
    COLOR_CLASS_CHOICES = (
        ("", _("None")),
        ("primary", "primary"),
        ("secondary", "secondary"),
        ("success", "success"),
        ("danger", "danger"),
        ("warning", "warning"),
        ("info", "info"),
        ("light", "light"),
        ("dark", "dark"),
        ("muted", "muted"),
        ("white", "white"),
    )
    name = models.CharField(_("name"), max_length=120)
    fg_color_class = models.CharField(
        _("bootstrap color class"),
        max_length=10,
        blank=True,
        choices=COLOR_CLASS_CHOICES,
        default="",
    )
    bg_color_class = models.CharField(
        _("bootstrap color class"),
        max_length=10,
        blank=True,
        choices=COLOR_CLASS_CHOICES,
        default="",
    )
    description = models.TextField(_("description"), blank=True, null=True)
    sort_order = models.IntegerField(_("sort order"), default=1000)
    allow_for_reputation = models.BooleanField(_("Allow for reputation"), default=True)
    allow_at_character_creation = models.BooleanField(
        _("Allow at character creation"), default=True
    )

    class Meta:
        translate = ("name", "description")
        verbose_name = _("template category")
        verbose_name_plural = _("template categories")
        ordering = ("sort_order",)

    def __str__(self):
        return self.name

    def child_item_qs(self, extension_qs=None):
        if extension_qs is not None:
            return self.template_set.for_extensions(extension_qs).distinct()
        return self.template_set.distinct()

    def as_dict(self, extension_qs=None):
        return {
            "name": self.name,
            "description": self.description,
            "objects": [
                obj.as_dict() for obj in self.child_item_qs(extension_qs=extension_qs)
            ],
        }

    def get_bg_color_class(self):
        if self.bg_color_class:
            return "bg-{}".format(self.bg_color_class)
        return ""

    def get_fg_color_class(self):
        if self.fg_color_class:
            return "text-{}".format(self.fg_color_class)
        return ""


class TemplateQuerySet(HomebrewQuerySet, ExtensionSelectQuerySet):
    pass


class Template(HomebrewModel, PhaseSixModel, metaclass=TransMeta):
    """
    A character creation template
    """

    objects = TemplateQuerySet.as_manager()

    name = models.CharField(_("name"), max_length=120)
    extensions = models.ManyToManyField("rules.Extension")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        models.CASCADE,
        verbose_name=_("created by"),
        null=True,
        blank=True,
    )
    category = models.ForeignKey(
        TemplateCategory, models.CASCADE, verbose_name=_("category")
    )

    rules = models.TextField(_("rules"), blank=True, null=True)
    show_rules_in_combat = models.BooleanField(
        _("Show rules in combat"),
        default=False,
        help_text=_("Show the rule as combat action on the combat tab."),
    )
    show_in_attack_dice_rolls = models.BooleanField(
        _("Show in attack dice rolls"),
        default=False,
        help_text=_("Show the name in attack dice rolls."),
    )
    quote = models.TextField(_("quote"), blank=True, null=True)
    quote_author = models.CharField(
        _("quote author"), max_length=50, null=True, blank=True
    )

    cost = models.IntegerField(verbose_name=_("cost"), default=1)
    is_mastery = models.BooleanField(_("is mastery"), default=False)

    class Meta:
        translate = ("name", "rules")
        verbose_name = _("character template")
        verbose_name_plural = _("character templates")
        ordering = ("category__sort_order",)

    def __str__(self):
        return self.name

    @admin.display(boolean=True)
    def has_quote(self):
        if self.quote:
            return True
        return False

    @admin.display(boolean=True)
    def has_rules(self):
        if self.rules:
            return True
        return False

    @property
    def has_allows_priest_action(self):
        return self.templatemodifier_set.filter(allows_priest_actions=True).exists()

    @property
    def is_magic_template(self):
        return self.templatemodifier_set.filter(
            Q(skill__is_magical=True)
            | Q(unlocks_spell_origin__isnull=False)
            | Q(aspect__in=["base_max_arcana", "base_spell_points"])
        ).exists()

    def as_dict(self):
        return {
            "name": self.name,
            "extensions": [
                {"name": e.name, "identifier": e.identifier, "icon": e.fa_icon_latex}
                for e in self.extensions.all()
            ],
            "rules": self.rules,
            "quote": self.quote,
            "quote_author": self.quote_author,
            "cost": self.cost,
            "is_mastery": self.is_mastery,
            "modifiers": modifiers_for_qs(self.templatemodifier_set.all()),
        }


class TemplateModifier(ModifierBase):
    template = models.ForeignKey(
        Template, verbose_name=_("template"), on_delete=models.CASCADE
    )

    def __str__(self):
        return self.template.name


class TemplateRequirement(models.Model, metaclass=TransMeta):
    template = models.ForeignKey(
        Template, verbose_name=_("template"), on_delete=models.CASCADE
    )
    required_template = models.ForeignKey(
        Template,
        on_delete=models.CASCADE,
        related_name="required_template_requirement_set",
        blank=True,
        null=True,
    )


class StatusEffect(PhaseSixModel, metaclass=TransMeta):
    objects = ExtensionSelectQuerySet.as_manager()

    extensions = models.ManyToManyField("rules.Extension")
    is_active = models.BooleanField(_("is active"), default=True)
    fa_icon_class = models.CharField(
        _("FA Icon Class"), max_length=30, default="fas fa-book"
    )
    color_class = models.CharField(
        _("color class"),
        max_length=20,
        choices=COLOR_CLASS_CHOICES,
        default="text-white",
    )
    name = models.CharField(_("name"), max_length=120)
    rules = models.TextField(_("rules"), blank=True, null=True)
    ordering = models.IntegerField(_("ordering"), default=100)

    class Meta:
        ordering = ("ordering",)
        translate = ("name", "rules")
        verbose_name = _("status effect")
        verbose_name_plural = _("status effects")

    def __str__(self):
        return self.name


class FoeType(models.Model, metaclass=TransMeta):
    name = models.CharField(_("name"), max_length=100)

    class Meta:
        translate = ("name",)
        verbose_name = _("foe type")
        verbose_name_plural = _("foe types")

    def __str__(self):
        return self.name

    def child_item_qs(self, extension_qs=None):
        if extension_qs is not None:
            return self.foe_set.for_extensions(extension_qs).distinct()
        return self.foe_set.all().distinct()

    def as_dict(self, extension_qs=None):
        return {
            "name": self.name,
            "objects": [
                obj.as_dict() for obj in self.child_item_qs(extension_qs=extension_qs)
            ],
        }


class FoeResistanceOrWeakness(models.Model, metaclass=TransMeta):
    name = models.CharField(_("name"), max_length=100)

    class Meta:
        translate = ("name",)
        verbose_name = _("foe resistance or weakness")
        verbose_name_plural = _("foe resistances or weaknesses")

    def __str__(self):
        return self.name


class FoeQuerySet(HomebrewQuerySet, ExtensionSelectQuerySet):
    pass


class Foe(HomebrewModel, ModelWithImage, PhaseSixModel, metaclass=TransMeta):
    objects = FoeQuerySet.as_manager()
    image_upload_to = "foe_images"

    extensions = models.ManyToManyField("rules.Extension")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        models.CASCADE,
        verbose_name=_("created by"),
        null=True,
        blank=True,
    )

    name = models.CharField(_("name"), max_length=120)
    short_description = models.TextField(_("short description"), blank=True, null=True)
    slug = models.SlugField(_("slug"), max_length=120, unique=True)

    type = models.ForeignKey(FoeType, verbose_name=_("type"), on_delete=models.CASCADE)
    wiki_page = models.OneToOneField(
        "worlds.WikiPage", blank=True, null=True, on_delete=models.SET_NULL
    )

    # Always present values
    health = models.IntegerField(_("health"), default=6)
    movement = models.IntegerField(_("movement"), default=4)

    strength = models.IntegerField(_("strength"), default=2)
    dexterity = models.IntegerField(_("dexterity"), default=2)
    mind = models.IntegerField(_("mind"), default=2)

    # Values only displayed if other than default

    actions = models.IntegerField(_("actions"), default=2)

    stress_test_succeeded_stress = models.IntegerField(
        _("stress test succeeded stress"), default=0
    )
    stress_test_failed_stress = models.IntegerField(
        _("stress test failed stress"), default=0
    )

    resistances = models.ManyToManyField(
        FoeResistanceOrWeakness,
        blank=True,
        related_name="foe_resistance_set",
        verbose_name=_("resistances"),
    )
    weaknesses = models.ManyToManyField(
        FoeResistanceOrWeakness,
        blank=True,
        related_name="foe_weakness_set",
        verbose_name=_("weaknesses"),
    )

    class Meta:
        translate = ("name", "short_description")
        verbose_name = _("foe")
        verbose_name_plural = _("foes")

    def __str__(self):
        return self.name

    def save(self, **kwargs):
        if not self.slug:
            unique_slugify(self, str(self.name_de))
        super().save(**kwargs)

    def may_edit(self, user):
        return user.is_superuser or user == self.created_by

    def get_image_url(self, geometry="180", crop="center"):
        if self.image:
            return get_thumbnail(self.image, geometry, crop=crop, quality=99).url

        return static_thumbnail(
            f"img/silhouette.png",
            geometry_string=geometry,
            crop=crop,
        )

    def as_dict(self):
        return {
            "name": self.name,
            "short_description": self.short_description,
            "type": self.type.name,
            "health": self.health,
            "movement": self.movement,
            "strength": self.strength,
            "dexterity": self.dexterity,
            "mind": self.mind,
            "stress_test_succeeded_stress": self.stress_test_succeeded_stress,
            "stress_test_failed_stress": self.stress_test_failed_stress,
            "resistances": [r.name for r in self.resistances.all()],
            "weaknesses": [w.name for w in self.weaknesses.all()],
            "actions": [action.as_dict() for action in self.foeaction_set.all()],
            "extensions": [e.identifier for e in self.extensions.all()],
        }


class FoeAction(HomebrewModel, metaclass=TransMeta):
    foe = models.ForeignKey(Foe, verbose_name=_("foe"), on_delete=models.CASCADE)
    name = models.CharField(_("name"), max_length=256)
    skill = models.IntegerField(_("skill"), default=6)
    effect = models.TextField(_("effect"))

    class Meta:
        translate = ("name", "effect")
        verbose_name = _("foe action")
        verbose_name_plural = _("foe actions")

    def as_dict(self):
        return {
            "name": self.name,
            "skill": self.skill,
            "effect": self.effect,
        }
