from django.db import models
from transmeta import TransMeta

from django.conf import settings
from django.utils.translation import gettext_lazy as _

from armory.mixins import SearchableCardListMixin
from homebrew.models import HomebrewModel, HomebrewQuerySet
from phasesix.models import PhaseSixModel
from rules.models import ExtensionSelectQuerySet


class RecipeDifficulty(models.Model, metaclass=TransMeta):
    name = models.CharField(_("name"), max_length=256)

    class Meta:
        translate = ("name",)
        verbose_name = _("recipe difficulty")
        verbose_name_plural = _("recipe difficulties")

    def __str__(self):
        return self.name


class RecipeQuerySet(ExtensionSelectQuerySet, HomebrewQuerySet):
    pass


class RecipeCategory(SearchableCardListMixin, PhaseSixModel, metaclass=TransMeta):
    name = models.CharField(_("name"), max_length=100)
    description = models.TextField(_("description"), blank=True, null=True)
    ordering = models.IntegerField(_("ordering"), default=10)

    class Meta:
        ordering = ("-ordering",)
        translate = ("name", "description")
        verbose_name = _("recipe category")
        verbose_name_plural = _("recipe categories")

    def __str__(self):
        return self.name

    def child_item_qs(self):
        return self.recipe_set.all()


class Recipe(HomebrewModel, PhaseSixModel, metaclass=TransMeta):
    objects = RecipeQuerySet.as_manager()

    category = models.ForeignKey(RecipeCategory, on_delete=models.CASCADE)
    extensions = models.ManyToManyField("rules.Extension")

    difficulty = models.ForeignKey(
        RecipeDifficulty, verbose_name=_("difficulty"), on_delete=models.CASCADE
    )

    name = models.CharField(_("name"), max_length=256)
    description = models.TextField(_("description"), blank=True, null=True)
    expected_amount = models.PositiveIntegerField(
        _("expected amount"), blank=True, null=True
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("created by"),
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )

    class Meta:
        translate = ("name", "description")
        verbose_name = _("recipe")
        verbose_name_plural = _("recipes")

    def __str__(self):
        return self.name


class RecipeIngredientUnit(models.Model, metaclass=TransMeta):
    name = models.CharField(_("name"), max_length=256)

    class Meta:
        translate = ("name",)
        verbose_name = _("recipe ingredient unit")
        verbose_name_plural = _("recipe ingredient units")

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    ingredient = models.ForeignKey("armory.Item", on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(_("quantity"))
    unit = models.ForeignKey(
        RecipeIngredientUnit,
        verbose_name=_("unit"),
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
