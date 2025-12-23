from django.db import models
from django.conf import settings
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from transmeta import TransMeta

from homebrew.models import HomebrewModel
from phasesix.models import ModelWithImage, PhaseSixModel
from rules.models import ExtensionSelectQuerySet, Extension


class EntityCategoryQuerySet(models.QuerySet):
    def for_extensions(self, extension_rm):
        return self.filter(
            Q(item__extensions__id__in=extension_rm.all())
            | Q(item__extensions__id__in=Extension.objects.filter(is_mandatory=True))
        ).distinct()


class EntityCategory(PhaseSixModel, metaclass=TransMeta):
    objects = EntityCategoryQuerySet.as_manager()

    name = models.CharField(_("name"), max_length=100)
    description = models.TextField(_("description"), blank=True, null=True)
    ordering = models.IntegerField(_("ordering"), default=10)

    class Meta:
        ordering = ("-ordering",)
        translate = ("name", "description")
        verbose_name = _("entity category")
        verbose_name_plural = _("entity categories")

    def __str__(self):
        return self.name


class Entity(HomebrewModel, ModelWithImage, PhaseSixModel, metaclass=TransMeta):
    objects = ExtensionSelectQuerySet.as_manager()
    image_upload_to = "entity_images/"

    category = models.ForeignKey(EntityCategory, on_delete=models.CASCADE)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("created by"),
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )

    extensions = models.ManyToManyField("rules.Extension")
    wiki_page = models.ForeignKey(
        "worlds.WikiPage", null=True, blank=True, on_delete=models.SET_NULL
    )

    name = models.CharField(_("name"), max_length=256)
    short_name = models.CharField(
        _("short name"),
        help_text=_("An optional short name for selections."),
        blank=True,
        null=True,
        max_length=90,
    )
    description = models.TextField(_("description"), blank=True, null=True)

    ordering = models.IntegerField(_("ordering"), default=100)

    class Meta:
        translate = ("name", "short_name", "description")
        verbose_name = _("entity")
        verbose_name_plural = _("entities")

    def __str__(self):
        return self.name


class PriestAction(HomebrewModel, PhaseSixModel, metaclass=TransMeta):
    WORK_TYPE_CHOICES = (
        ("lesser", _("Lesser")),
        ("higher", _("Higher")),
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("created by"),
    )
    grace_cost = models.IntegerField(_("grace cost"))
    work_type = models.CharField(
        _("work type"), max_length=6, choices=WORK_TYPE_CHOICES, blank=True, null=True
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
        translate = ("name", "rules")
        verbose_name = _("priest action")
        verbose_name_plural = _("priest actions")


class PriestActionRoll(models.Model, metaclass=TransMeta):
    priest_action = models.ForeignKey(
        PriestAction, verbose_name=_("priest action"), on_delete=models.CASCADE
    )
    attribute = models.ForeignKey(
        "rules.Attribute",
        verbose_name=_("attribute for usage"),
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )
    custom_roll_name = models.CharField(
        _("custom roll name"), max_length=80, blank=True, null=True
    )
    custom_roll_dice = models.CharField(
        _("custom roll dice"), max_length=20, blank=True, null=True
    )

    class Meta:
        translate = ("custom_roll_name",)
        verbose_name = _("priest action roll")
        verbose_name_plural = _("priest action rolls")

    def __str__(self):
        if self.custom_roll_name_de is not None or self.custom_roll_name_en is not None:
            return self.custom_roll_name
        return self.attribute.name
