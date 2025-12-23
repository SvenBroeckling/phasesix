from django.db import models
from django.utils.translation import gettext_lazy as _
from transmeta import TransMeta

from armory.mixins import SearchableCardListMixin
from homebrew.models import HomebrewModel, HomebrewQuerySet
from phasesix.models import PhaseSixModel
from rules.models import ModifierBase, modifiers_for_qs
from rules.models import Skill, Attribute, Knowledge


class QuirkCategory(SearchableCardListMixin, models.Model, metaclass=TransMeta):
    name = models.CharField(_("name"), max_length=30)

    class Meta:
        ordering = ("id",)
        translate = ("name",)
        verbose_name = _("quirk category")
        verbose_name_plural = _("quirk categories")

    def __str__(self):
        return self.name

    def child_item_qs(self, extension_qs=None):
        # TODO: Implement extensions on quirks
        return self.quirk_set.distinct()

    def as_dict(self, extension_qs=None):
        return {
            "name": self.name,
            "objects": [
                obj.as_dict() for obj in self.child_item_qs(extension_qs=extension_qs)
            ],
        }


class Quirk(HomebrewModel, PhaseSixModel, metaclass=TransMeta):
    objects = HomebrewQuerySet.as_manager()

    name = models.CharField(_("name"), max_length=60)
    category = models.ForeignKey(
        QuirkCategory, verbose_name=_("category"), on_delete=models.CASCADE
    )
    positive_effects = models.TextField(_("positive effects"), blank=True, null=True)
    negative_effects = models.TextField(_("negative effects"), blank=True, null=True)
    description = models.TextField(_("description"), blank=True, null=True)

    class Meta:
        ordering = ("id",)
        translate = ("name", "description", "positive_effects", "negative_effects")
        verbose_name = _("quirk")
        verbose_name_plural = _("quirks")

    def __str__(self):
        return self.name

    def as_dict(self):
        return {
            "name": self.name,
            "category": self.category.name,
            "description": self.description,
            "positive_effects": self.positive_effects,
            "negative_effects": self.negative_effects,
            "modifiers": modifiers_for_qs(self.quirkmodifier_set.all()),
        }


class QuirkModifier(ModifierBase):
    quirk = models.ForeignKey(Quirk, verbose_name=_("quirk"), on_delete=models.CASCADE)
