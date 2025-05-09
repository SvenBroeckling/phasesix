import itertools

from django.conf import settings
from django.contrib import admin
from django.db import models
from django.db.models import Q, Sum
from django.utils.translation import gettext_lazy as _
from transmeta import TransMeta

from armory.choices import COLOR_CLASS_CHOICES
from armory.mixins import SearchableCardListMixin
from homebrew.models import HomebrewModel, HomebrewQuerySet

CHARACTER_ASPECT_CHOICES = (
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
    def for_world(self, world):
        q = Q(is_mandatory=True)
        if world.extension:
            q |= Q(pk=world.extension.pk)
        if world.extension.fixed_epoch:
            q |= Q(pk=world.extension.fixed_epoch.pk)
        q |= Q(pk__in=world.extension.fixed_extensions.all())
        return self.filter(q)

    def first_class_extensions(self):
        return self.filter(Q(type="e") | Q(is_mandatory=True)).filter(is_active=True)


class Extension(models.Model, metaclass=TransMeta):
    """
    A PhaseSix source book extension
    """

    EXTENSION_TYPE_CHOICES = (
        ("x", _("Extension")),
        ("e", _("Epoch")),
        ("w", _("World")),
    )
    objects = ExtensionQuerySet.as_manager()

    is_mandatory = models.BooleanField(_("is mandatory"), default=False)
    is_active = models.BooleanField(_("is active"), default=True)
    type = models.CharField(
        _("type"), max_length=1, choices=EXTENSION_TYPE_CHOICES, default="x"
    )

    name = models.CharField(_("name"), max_length=120)
    identifier = models.CharField(_("identifier"), max_length=20)
    description = models.TextField(_("description"), blank=True, null=True)

    year_range = models.CharField(_("year range"), blank=True, null=True, max_length=50)
    fa_icon_class = models.CharField(
        _("FA Icon Class"), max_length=30, default="fas fa-book"
    )

    image = models.ImageField(
        _("image"), upload_to="extension_images", max_length=256, blank=True, null=True
    )
    image_copyright = models.CharField(
        _("image copyright"), max_length=40, blank=True, null=True
    )
    image_copyright_url = models.CharField(
        _("image copyright url"), max_length=150, blank=True, null=True
    )

    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    modified_at = models.DateTimeField(_("modified at"), auto_now=True)
    ordering = models.IntegerField(_("ordering"), default=100)

    # only world related
    currency_map = models.ForeignKey(
        "armory.CurrencyMap", blank=True, null=True, on_delete=models.SET_NULL
    )
    fixed_extensions = models.ManyToManyField(
        "self", blank=True, limit_choices_to={"type": "x"}
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


class Lineage(models.Model, metaclass=TransMeta):
    objects = ExtensionSelectQuerySet.as_manager()

    name = models.CharField(_("name"), max_length=80)
    description = models.TextField(_("description"), blank=True, null=True)

    extensions = models.ManyToManyField("rules.Extension")
    template = models.ForeignKey(
        "rules.Template", blank=True, null=True, on_delete=models.SET_NULL
    )

    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    modified_at = models.DateTimeField(_("modified at"), auto_now=True)

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
    base_max_stress = models.IntegerField(_("max stress"), default=6)
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


class Knowledge(models.Model, metaclass=TransMeta):
    objects = ExtensionSelectQuerySet.as_manager()

    name = models.CharField(_("name"), max_length=120)
    extensions = models.ManyToManyField("rules.Extension")
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    modified_at = models.DateTimeField(_("modified at"), auto_now=True)
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

    def child_item_qs(self):
        return self.template_set.all()

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


class Template(HomebrewModel, metaclass=TransMeta):
    """
    A character creation template
    """

    objects = TemplateQuerySet.as_manager()

    name = models.CharField(_("name"), max_length=120)
    extensions = models.ManyToManyField("rules.Extension")
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        models.CASCADE,
        verbose_name=_("created by"),
        null=True,
        blank=True,
    )
    modified_at = models.DateTimeField(_("modified at"), auto_now=True)
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


class StatusEffect(models.Model, metaclass=TransMeta):
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
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    modified_at = models.DateTimeField(_("modified at"), auto_now=True)
    ordering = models.IntegerField(_("ordering"), default=100)

    class Meta:
        ordering = ("ordering",)
        translate = ("name", "rules")
        verbose_name = _("status effect")
        verbose_name_plural = _("status effects")

    def __str__(self):
        return self.name
