from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from transmeta import TransMeta

from armory.models import RARITY_CHOICES
from homebrew.models import HomebrewModel, HomebrewQuerySet
from phasesix.models import ModelWithImage, PhaseSixModel
from rules.models import ModifierBase, modifiers_for_qs, ExtensionSelectQuerySet


class SocketLocation(models.Model, metaclass=TransMeta):
    name = models.CharField(_("name"), max_length=30)
    identifier = models.CharField(_("identifier"), max_length=30)
    gi_icon_class = models.CharField(_("gi icon class"), blank=True, null=True)

    class Meta:
        ordering = ("id",)
        translate = ("name",)
        verbose_name = _("socket location")
        verbose_name_plural = _("socket locations")

    def __str__(self):
        return self.name


class BodyModificationType(ModelWithImage, metaclass=TransMeta):
    name = models.CharField(_("name"), max_length=30)
    image_upload_to = "body_modification_type_images"

    class Meta:
        ordering = ("id",)
        translate = ("name",)
        verbose_name = _("body modification type")
        verbose_name_plural = _("body modification types")

    def __str__(self):
        return self.name

    def child_item_qs(self, extension_qs=None):
        if extension_qs is not None:
            return self.bodymodification_set.for_extensions(extension_qs).distinct()
        return self.bodymodification_set.distinct()

    def as_dict(self, extension_qs=None):
        return {
            "name": self.name,
            "objects": [
                obj.as_dict() for obj in self.child_item_qs(extension_qs=extension_qs)
            ],
        }


class BodyModificationQuerySet(HomebrewQuerySet, ExtensionSelectQuerySet):
    pass


class BodyModification(HomebrewModel, ModelWithImage, PhaseSixModel, metaclass=TransMeta):
    ACTIVATION_TYPES = (
        ("a", _("active")),
        ("p", _("passive")),
    )
    objects = BodyModificationQuerySet.as_manager()
    image_upload_to = "body_modification_images"
    type = models.ForeignKey(
        BodyModificationType, verbose_name=_("type"), on_delete=models.CASCADE
    )
    extensions = models.ManyToManyField("rules.Extension")

    activation = models.CharField(
        _("activation"), max_length=1, default="p", choices=ACTIVATION_TYPES
    )
    price = models.DecimalField(_("price"), decimal_places=2, max_digits=6)
    rarity = models.CharField(
        _("rarity"), max_length=1, default="c", choices=RARITY_CHOICES
    )
    bio_strain = models.IntegerField(_("bio strain"), default=1)
    energy_consumption_ma = models.IntegerField(_("energy consumption (mA)"), default=1)
    charges = models.IntegerField(_("charges"), null=True, blank=True)
    usable_in_combat = models.BooleanField(_("usable in combat"), default=False)
    attribute = models.ForeignKey(
        "rules.Attribute",
        verbose_name=_("attribute for usage"),
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )
    skill = models.ForeignKey(
        "rules.Skill",
        verbose_name=_("skill for usage"),
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )
    knowledge = models.ForeignKey(
        "rules.Knowledge",
        verbose_name=_("knowledge for usage"),
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )

    dice_roll_string = models.CharField(
        _("dice role string"),
        blank=True,
        null=True,
        max_length=10,
        help_text=_("Shows a roll button at the item if not empty."),
    )

    name = models.CharField(_("name"), max_length=80)
    description = models.TextField(_("description"))
    rules = models.TextField(_("rules"), blank=True, null=True)
    quote = models.TextField(_("quote"), blank=True, null=True)
    quote_author = models.CharField(
        _("quote author"), max_length=50, null=True, blank=True
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("created by"),
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )

    class Meta:
        ordering = ("id",)
        translate = (
            "name",
            "description",
            "rules",
        )
        verbose_name = _("body modification")
        verbose_name_plural = _("body modifications")

    def __str__(self):
        return self.name

    def as_dict(self):
        return {
            "id": self.id,
            "type": self.type.name,
            "name": self.name,
            "description": self.description,
            "rules": self.rules,
            "quote": self.quote,
            "quote_author": self.quote_author,
            "activation": self.get_activation_display(),
            "price": int(self.price),
            "rarity": self.get_rarity_display(),
            "bio_strain": self.bio_strain,
            "energy_consumption_ma": self.energy_consumption_ma,
            "charges": self.charges,
            "usable_in_combat": self.usable_in_combat,
            "attribute": self.attribute.name if self.attribute else None,
            "skill": self.skill.name if self.skill else None,
            "knowledge": self.knowledge.name if self.knowledge else None,
            "dice_roll_string": self.dice_roll_string,
            "image": self.image.url if self.image else None,
            "image_copyright": self.image_copyright,
            "image_copyright_url": self.image_copyright_url,
            "socket_locations": [
                f"{sl.socket_location.name} ({sl.socket_amount})"
                for sl in self.bodymodificationsocketlocation_set.all()
            ],
            "modifiers": modifiers_for_qs(self.bodymodificationmodifier_set.all()),
        }


class BodyModificationSocketLocation(models.Model):
    body_modification = models.ForeignKey(BodyModification, on_delete=models.CASCADE)
    socket_location = models.ForeignKey(
        SocketLocation, verbose_name=_("socket location"), on_delete=models.CASCADE
    )
    socket_amount = models.IntegerField(_("socket amount"), default=1)

    class Meta:
        ordering = ("id",)
        verbose_name = _("body modification socket location")
        verbose_name_plural = _("body modification socket locations")


class BodyModificationModifier(ModifierBase):
    body_modification = models.ForeignKey(
        BodyModification, verbose_name=_("body modification"), on_delete=models.CASCADE
    )

    class Meta:
        ordering = ("id",)
        verbose_name = _("body modification modifier")
        verbose_name_plural = _("body modification modifiers")

    def __str__(self):
        return self.body_modification.name
