from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from transmeta import TransMeta

from armory.mixins import SearchableCardListMixin
from homebrew.models import HomebrewModel, HomebrewQuerySet

SPELL_ATTRIBUTE_CHOICES = (
    ("power", _("power")),
    ("range", _("range")),
    ("actions", _("actions")),
    ("arcana_cost", _("arcana")),
)


class SpellVariant(models.Model, metaclass=TransMeta):
    name = models.CharField(_("name"), max_length=30)

    class Meta:
        ordering = ("id",)
        translate = ("name",)
        verbose_name = _("spell variant")
        verbose_name_plural = _("spell variants")

    def __str__(self):
        return self.name


class SpellShape(models.Model, metaclass=TransMeta):
    name = models.CharField(_("name"), max_length=30)

    class Meta:
        ordering = ("id",)
        translate = ("name",)
        verbose_name = _("spell shape")
        verbose_name_plural = _("spell shapes")

    def __str__(self):
        return self.name


class SpellType(models.Model, metaclass=TransMeta):
    name = models.CharField(_("name"), max_length=30)
    fa_icon_class = models.CharField(
        _("FA Icon Class"), max_length=30, default="fas fa-book"
    )
    image = models.ImageField(
        _("image"), upload_to="spelltype_images", max_length=256, blank=True, null=True
    )
    image_copyright = models.CharField(
        _("image copyright"), max_length=40, blank=True, null=True
    )
    image_copyright_url = models.CharField(
        _("image copyright url"), max_length=150, blank=True, null=True
    )

    reference_attribute = models.ForeignKey(
        "rules.Attribute",
        verbose_name=_("reference attribute"),
        on_delete=models.CASCADE,
    )

    class Meta:
        ordering = ("id",)
        translate = ("name",)
        verbose_name = _("spell type")
        verbose_name_plural = _("spell types")

    def __str__(self):
        return self.name


class SpellOrigin(SearchableCardListMixin, models.Model, metaclass=TransMeta):
    name = models.CharField(_("name"), max_length=30)
    fa_icon_class = models.CharField(
        _("FA Icon Class"), max_length=30, default="fas fa-book"
    )
    image = models.ImageField(
        _("image"),
        upload_to="spellorigin_images",
        max_length=256,
        blank=True,
        null=True,
    )
    image_copyright = models.CharField(
        _("image copyright"), max_length=40, blank=True, null=True
    )
    image_copyright_url = models.CharField(
        _("image copyright url"), max_length=150, blank=True, null=True
    )

    class Meta:
        ordering = ("id",)
        translate = ("name",)
        verbose_name = _("spell origin")
        verbose_name_plural = _("spell origins")

    def __str__(self):
        return self.name

    def child_item_qs(self):
        return self.basespell_set.all()


class BaseSpell(HomebrewModel, metaclass=TransMeta):
    objects = HomebrewQuerySet.as_manager()
    DURATION_UNITS = (
        ("actions", _("actions")),
        ("rounds", _("rounds")),
        ("seconds", _("seconds")),
        ("minutes", _("minutes")),
        ("hours", _("hours")),
        ("days", _("days")),
        ("nights", _("nights")),
        ("weeks", _("weeks")),
        ("months", _("months")),
        ("years", _("years")),
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("created by"),
    )

    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    modified_at = models.DateTimeField(_("modified at"), auto_now=True)

    spell_point_cost = models.IntegerField(_("spell point cost"))
    arcana_cost = models.IntegerField(_("arcana cost"), default=1)

    range = models.IntegerField(_("range"), default=0)
    actions = models.IntegerField(_("actions"), default=1)
    duration = models.CharField(
        _("duration"),
        max_length=40,
        blank=True,
        null=True,
        help_text=_("Leave empty for instantaneous spells"),
    )
    duration_unit = models.CharField(
        _("duration unit"), max_length=10, choices=DURATION_UNITS, blank=True, null=True
    )
    needs_concentration = models.BooleanField(_("needs concentration"), default=False)
    is_ritual = models.BooleanField(_("is ritual"), default=False)

    type = models.ForeignKey(
        SpellType, on_delete=models.CASCADE, verbose_name=_("type")
    )
    origin = models.ForeignKey(
        SpellOrigin,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_("origin"),
    )
    variant = models.ForeignKey(
        SpellVariant, on_delete=models.CASCADE, verbose_name=_("variant")
    )
    shape = models.ForeignKey(
        SpellShape,
        on_delete=models.CASCADE,
        verbose_name=_("shape"),
        blank=True,
        null=True,
    )

    name = models.CharField(_("name"), max_length=80)
    rules = models.TextField(_("rules"))
    quote = models.TextField(_("quote"), blank=True, null=True)
    quote_author = models.CharField(
        _("quote author"), max_length=50, null=True, blank=True
    )

    def __str__(self):
        return self.name

    class Meta:
        ordering = ("id",)
        translate = ("name", "rules", "duration")
        verbose_name = _("base spell")
        verbose_name_plural = _("base spells")


class SpellTemplateCategory(models.Model, metaclass=TransMeta):
    name = models.CharField(_("name"), max_length=120)

    class Meta:
        translate = ("name",)
        verbose_name = _("spell template category")
        verbose_name_plural = _("spell template categories")

    def __str__(self):
        return self.name


class SpellTemplate(models.Model, metaclass=TransMeta):
    name = models.CharField(_("name"), max_length=120)
    category = models.ForeignKey(SpellTemplateCategory, on_delete=models.CASCADE)

    spell_point_cost = models.IntegerField(
        verbose_name=_("spell point cost"), default=1
    )

    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    modified_at = models.DateTimeField(_("modified at"), auto_now=True)

    rules = models.TextField(_("rules"), blank=True, null=True)

    quote = models.TextField(_("quote"), blank=True, null=True)
    quote_author = models.CharField(
        _("quote author"), max_length=50, null=True, blank=True
    )

    class Meta:
        translate = ("name", "rules")
        verbose_name = _("spell template")
        verbose_name_plural = _("spell templates")

    def __str__(self):
        return self.name


class SpellTemplateModifier(models.Model, metaclass=TransMeta):
    spell_template = models.ForeignKey(SpellTemplate, on_delete=models.CASCADE)
    attribute = models.CharField(
        verbose_name=_("attribute"),
        max_length=40,
        choices=SPELL_ATTRIBUTE_CHOICES,
        null=True,
        blank=True,
    )
    attribute_modifier = models.IntegerField(
        verbose_name=_("attribute modifier"), blank=True, null=True
    )
    variant_change = models.ForeignKey(
        SpellVariant,
        on_delete=models.SET_NULL,
        verbose_name=_("variant change"),
        null=True,
        blank=True,
    )
    type_change = models.ForeignKey(
        SpellType,
        on_delete=models.SET_NULL,
        verbose_name=_("type change"),
        null=True,
        blank=True,
    )
    shape_change = models.ForeignKey(
        SpellShape,
        on_delete=models.SET_NULL,
        verbose_name=_("shape change"),
        null=True,
        blank=True,
    )
