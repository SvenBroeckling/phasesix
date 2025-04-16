from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from transmeta import TransMeta

from armory.models import RARITY_CHOICES
from homebrew.models import HomebrewModel, HomebrewQuerySet
from rules.models import ModifierBase


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


class BodyModificationType(models.Model, metaclass=TransMeta):
    name = models.CharField(_("name"), max_length=30)

    image = models.ImageField(
        _("image"),
        upload_to="body_modification_type_images",
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

    def __str__(self):
        return self.name

    class Meta:
        ordering = ("id",)
        translate = ("name",)
        verbose_name = _("body modification type")
        verbose_name_plural = _("body modification types")

    def child_item_qs(self):
        return self.bodymodification_set.all()


class BodyModificationQuerySet(HomebrewQuerySet):
    pass


class BodyModification(HomebrewModel, metaclass=TransMeta):
    ACTIVATION_TYPES = (
        ("a", _("active")),
        ("p", _("passive")),
    )
    objects = BodyModificationQuerySet.as_manager()
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

    image = models.ImageField(
        _("image"),
        upload_to="body_modification_images",
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

    name = models.CharField(_("name"), max_length=80)
    description = models.TextField(_("description"))
    rules = models.TextField(_("rules"), blank=True, null=True)
    quote = models.TextField(_("quote"), blank=True, null=True)
    quote_author = models.CharField(
        _("quote author"), max_length=50, null=True, blank=True
    )

    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
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
