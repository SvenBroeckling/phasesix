from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from transmeta import TransMeta

from armory.mixins import SearchableCardListMixin
from homebrew.models import HomebrewModel, HomebrewQuerySet
from phasesix.models import ModelWithImage, PhaseSixModel

SPELL_ATTRIBUTE_CHOICES = (
    ("power", _("Power")),
    ("range", _("Range")),
    ("actions", _("Actions")),
    ("arcana_cost", _("Arcana")),
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


class SpellType(ModelWithImage, metaclass=TransMeta):
    name = models.CharField(_("name"), max_length=30)
    fa_icon_class = models.CharField(
        _("FA Icon Class"), max_length=30, default="fas fa-book"
    )
    image_upload_to = "spelltype_images"

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


class SpellOrigin(SearchableCardListMixin, ModelWithImage, metaclass=TransMeta):
    name = models.CharField(_("name"), max_length=30)
    fa_icon_class = models.CharField(
        _("FA Icon Class"), max_length=30, default="fas fa-book"
    )
    image_upload_to = "spellorigin_images"

    class Meta:
        ordering = ("id",)
        translate = ("name",)
        verbose_name = _("spell origin")
        verbose_name_plural = _("spell origins")

    def __str__(self):
        return self.name

    def child_item_qs(self, extension_qs=None):
        # TODO: Implement extensions on basespells
        return self.basespell_set.distinct()

    def as_dict(self, extension_qs=None):
        return {
            "name": self.name,
            "fa_icon_class": self.fa_icon_class,
            "image": self.image.url if self.image else None,
            "image_copyright": self.image_copyright,
            "image_copyright_url": self.image_copyright_url,
            "objects": [
                obj.as_dict() for obj in self.child_item_qs(extension_qs=extension_qs)
            ],
        }


class BaseSpell(HomebrewModel, PhaseSixModel, metaclass=TransMeta):
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

    class Meta:
        ordering = ("id",)
        translate = ("name", "rules", "duration")
        verbose_name = _("base spell")
        verbose_name_plural = _("base spells")

    def __str__(self):
        return self.name

    def as_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "spell_point_cost": self.spell_point_cost,
            "arcana_cost": self.arcana_cost,
            "range": self.range,
            "actions": self.actions,
            "duration": self.duration,
            "duration_unit": self.get_duration_unit_display(),
            "needs_concentration": self.needs_concentration,
            "is_ritual": self.is_ritual,
            "type": {
                "id": self.type.id,
                "name": self.type.name,
            },
            "origin": (
                {
                    "id": self.origin.id,
                    "name": self.origin.name,
                }
                if self.origin
                else None
            ),
            "variant": {
                "id": self.variant.id,
                "name": self.variant.name,
            },
            "shape": (
                {
                    "id": self.shape.id,
                    "name": self.shape.name,
                }
                if self.shape
                else None
            ),
            "rules": self.rules,
            "quote": self.quote,
            "quote_author": self.quote_author,
        }


class SpellTemplateCategory(models.Model, metaclass=TransMeta):
    name = models.CharField(_("name"), max_length=120)

    class Meta:
        translate = ("name",)
        verbose_name = _("spell template category")
        verbose_name_plural = _("spell template categories")

    def __str__(self):
        return self.name

    def child_item_qs(self, extension_qs=None):
        # TODO: Implement extensions on spelltemplates
        return self.spelltemplate_set.distinct()

    def as_dict(self, extension_qs=None):
        return {
            "name": self.name,
            "objects": [
                obj.as_dict() for obj in self.child_item_qs(extension_qs=extension_qs)
            ],
        }


class SpellTemplate(PhaseSixModel, metaclass=TransMeta):
    name = models.CharField(_("name"), max_length=120)
    category = models.ForeignKey(SpellTemplateCategory, on_delete=models.CASCADE)

    spell_point_cost = models.IntegerField(
        verbose_name=_("spell point cost"), default=1
    )

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

    def as_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "spell_point_cost": self.spell_point_cost,
            "category": {
                "id": self.category.id,
                "name": self.category.name,
            },
            "rules": self.rules,
            "quote": self.quote,
            "modifiers": [
                modifier.as_dict() for modifier in self.spelltemplatemodifier_set.all()
            ],
        }


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

    class Meta:
        verbose_name = _("spell template modifier")
        verbose_name_plural = _("spell template modifiers")

    def as_dict(self):
        return {
            "id": self.id,
            "attribute": self.get_attribute_display(),
            "attribute_modifier": self.attribute_modifier,
            "variant_change": (
                {
                    "id": self.variant_change.id,
                    "name": self.variant_change.name,
                }
                if self.variant_change
                else None
            ),
            "type_change": (
                {
                    "id": self.type_change.id,
                    "name": self.type_change.name,
                }
                if self.type_change
                else None
            ),
            "shape_change": (
                {
                    "id": self.shape_change.id,
                    "name": self.shape_change.name,
                }
                if self.shape_change
                else None
            ),
        }
