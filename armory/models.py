from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from transmeta import TransMeta

from armory.choices import (
    COLOR_CLASS_CHOICES,
    PROTECTION_FA_ICON_CLASS_CHOICES,
    CURRENCY_FA_ICON_CLASS_CHOICES,
)
from armory.mixins import SearchableCardListMixin
from homebrew.models import HomebrewModel, HomebrewQuerySet
from rules.models import ExtensionSelectQuerySet, Extension


class ItemTypeQuerySet(models.QuerySet):
    def for_extensions(self, extension_rm):
        return self.filter(
            Q(item__extensions__id__in=extension_rm.all())
            | Q(item__extensions__id__in=Extension.objects.filter(is_mandatory=True))
        ).distinct()


class ItemType(SearchableCardListMixin, models.Model, metaclass=TransMeta):
    objects = ItemTypeQuerySet.as_manager()

    name = models.CharField(_("name"), max_length=100)
    description = models.TextField(_("description"), blank=True, null=True)
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    modified_at = models.DateTimeField(_("modified at"), auto_now=True)
    ordering = models.IntegerField(_("ordering"), default=10)

    class Meta:
        ordering = ("-ordering",)
        translate = ("name", "description")
        verbose_name = _("item type")
        verbose_name_plural = _("item types")

    def __str__(self):
        return self.name

    def child_item_qs(self):
        return self.item_set.all()


class ItemQuerySet(ExtensionSelectQuerySet, HomebrewQuerySet):
    pass


class Item(HomebrewModel, metaclass=TransMeta):
    objects = ItemQuerySet.as_manager()

    name = models.CharField(_("name"), max_length=256)
    description = models.TextField(_("description"), blank=True, null=True)

    type = models.ForeignKey(ItemType, verbose_name=_("type"), on_delete=models.CASCADE)
    is_container = models.BooleanField(_("is container"), default=False)

    weight = models.DecimalField(_("weight"), decimal_places=2, max_digits=6)
    price = models.DecimalField(_("price"), decimal_places=2, max_digits=6)
    concealment = models.IntegerField(_("concealment"), default=0)
    extensions = models.ManyToManyField("rules.Extension", blank=True)
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("created by"),
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )

    charges = models.IntegerField(_("charges"), null=True, blank=True)

    modified_at = models.DateTimeField(_("modified at"), auto_now=True)
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
        _("image"), max_length=256, upload_to="item_images/", null=True, blank=True
    )
    image_copyright = models.CharField(
        _("image copyright"), max_length=40, blank=True, null=True
    )
    image_copyright_url = models.CharField(
        _("image copyright url"), max_length=150, blank=True, null=True
    )

    class Meta:
        translate = ("name", "description")
        verbose_name = _("item")
        verbose_name_plural = _("items")

    def __str__(self):
        return self.name

    def get_image_thumbnail(self):
        return None  # TODO: Check if it is possible to make this beautiful in _gear_item.html
        # if not self.image:
        #     return None
        # thumbnail = get_thumbnail(self.image, "100x20", crop="center")
        # return thumbnail.url


class WeaponTypeQuerySet(models.QuerySet):
    def for_extensions(self, extension_rm):
        return self.filter(
            Q(weapon__extensions__id__in=extension_rm.all())
            | Q(weapon__extensions__id__in=Extension.objects.filter(is_mandatory=True))
        ).distinct()


class WeaponType(SearchableCardListMixin, models.Model, metaclass=TransMeta):
    objects = WeaponTypeQuerySet.as_manager()

    name = models.CharField(_("name"), max_length=100)
    description = models.TextField(_("description"), blank=True, null=True)
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    modified_at = models.DateTimeField(_("modified at"), auto_now=True)
    ordering = models.IntegerField(_("ordering"), default=10)

    class Meta:
        ordering = ("-ordering",)
        translate = ("name", "description")
        verbose_name = _("weapon type")
        verbose_name_plural = _("weapon types")

    def __str__(self):
        return self.name

    def get_first_image(self):
        return self.weapon_set.earliest("id").image

    def child_item_qs(self):
        return self.weapon_set.all()


RANGE_CHOICES = (
    ("-", _("hand to hand 1m")),
    ("+", _("hand to hand 2m")),
    ("s", _("short")),
    ("m", _("mid")),
    ("l", _("long")),
    ("e", _("extreme")),
)


class AttackMode(models.Model, metaclass=TransMeta):
    name = models.CharField(_("name"), max_length=100)
    dice_bonus = models.IntegerField(_("dice bonus"), default=1)
    capacity_consumed = models.IntegerField(_("capacity consumed"), default=1)

    class Meta:
        translate = ("name",)
        verbose_name = _("attack mode")
        verbose_name_plural = _("attack modes")

    def __str__(self):
        return self.name


class WeaponQuerySet(ExtensionSelectQuerySet, HomebrewQuerySet):
    pass


class Weapon(HomebrewModel, metaclass=TransMeta):
    objects = WeaponQuerySet.as_manager()

    extensions = models.ManyToManyField("rules.Extension", blank=True)
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    modified_at = models.DateTimeField(_("modified at"), auto_now=True)

    is_hand_to_hand_weapon = models.BooleanField(
        _("is hand to hand weapon"), default=False
    )
    is_throwing_weapon = models.BooleanField(_("is throwing weapon"), default=False)

    name = models.CharField(_("name"), max_length=256)
    description = models.TextField(_("description"), blank=True, null=True)
    attack_modes = models.ManyToManyField(AttackMode, verbose_name=_("attack modes"))

    type = models.ForeignKey(
        WeaponType, verbose_name=_("type"), on_delete=models.CASCADE
    )

    weight = models.DecimalField(_("weight"), decimal_places=2, max_digits=6)
    price = models.DecimalField(_("price"), decimal_places=2, max_digits=8)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("created by"),
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )

    image = models.ImageField(
        _("image"), max_length=256, upload_to="weapon_images/", null=True, blank=True
    )
    image_copyright = models.CharField(
        _("image copyright"), max_length=40, blank=True, null=True
    )
    image_copyright_url = models.CharField(
        _("image copyright url"), max_length=150, blank=True, null=True
    )

    class Meta:
        translate = ("name", "description")
        verbose_name = _("weapon")
        verbose_name_plural = _("weapons")

    def __str__(self):
        return self.name


class Keyword(models.Model, metaclass=TransMeta):
    identifier = models.CharField(_("identifier"), max_length=40, unique=True)
    name = models.CharField(_("name"), max_length=256)
    description = models.TextField(_("description"), blank=True, null=True)
    is_rare = models.BooleanField(_("is rare"), default=False)
    is_evergreen = models.BooleanField(
        _("is evergreen"),
        default=False,
        help_text=_("Evergreen keywords are the base of the combat mechanics."),
    )
    show_in_dice_rolls = models.BooleanField(_("show in dice rolls"), default=False)
    show_in_summary = models.BooleanField(_("show in summary"), default=False)
    ordering = models.IntegerField(_("ordering"), default=10)

    class Meta:
        translate = ("name", "description")
        verbose_name = _("keyword")
        verbose_name_plural = _("keywords")
        ordering = ("-ordering",)

    def __str__(self):
        return self.name


class WeaponKeyword(models.Model):
    weapon = models.ForeignKey("armory.Weapon", on_delete=models.CASCADE)
    keyword = models.ForeignKey("armory.Keyword", on_delete=models.CASCADE)
    value = models.IntegerField(_("value"), default=1)

    class Meta:
        verbose_name = _("weapon keyword")
        verbose_name_plural = _("weapon keywords")

    def __str__(self):
        return self.keyword.name


class WeaponModificationTypeQuerySet(models.QuerySet):
    def for_extensions(self, extension_rm):
        return self.filter(
            Q(weaponmodification__extensions__id__in=extension_rm.all())
            | Q(
                weaponmodification__extensions__id__in=Extension.objects.filter(
                    is_mandatory=True
                )
            )
        ).distinct()


class WeaponModificationType(models.Model, metaclass=TransMeta):
    objects = WeaponModificationTypeQuerySet.as_manager()

    name = models.CharField(_("name"), max_length=20)
    description = models.TextField(_("description"), blank=True, null=True)
    unique_equip = models.BooleanField(
        _("unique equip"),
        default=False,
        help_text=_(
            "A weapon may only have one modification of this type (i.E. sights)"
        ),
    )

    class Meta:
        translate = ("name", "description")
        verbose_name = _("weapon modification type")
        verbose_name_plural = _("weapon modification type")

    def __str__(self):
        return self.name


class WeaponModification(models.Model, metaclass=TransMeta):
    objects = ExtensionSelectQuerySet.as_manager()

    extensions = models.ManyToManyField("rules.Extension", blank=True)
    available_for_weapon_types = models.ManyToManyField(WeaponType)
    name = models.CharField(_("name"), max_length=40)
    description = models.TextField(_("description"), blank=True, null=True)
    rules = models.TextField(
        _("rules"),
        help_text=_(
            "Rules for this weapon modification. May be blank if only attribute changes apply."
        ),
        blank=True,
        null=True,
    )
    type = models.ForeignKey(WeaponModificationType, on_delete=models.CASCADE)
    price = models.DecimalField(_("price"), decimal_places=2, max_digits=6)

    class Meta:
        translate = ("name", "description", "rules")
        verbose_name = _("weapon modification")
        verbose_name_plural = _("weapon modification")

    def __str__(self):
        return self.name

    def extension_string(self):
        return ", ".join([e.identifier for e in self.extensions.all()])


class WeaponModificationKeyword(models.Model):
    weapon_modification = models.ForeignKey(
        WeaponModification, on_delete=models.CASCADE
    )
    keyword = models.ForeignKey("armory.Keyword", on_delete=models.CASCADE)
    value = models.IntegerField(_("value"), default=0)


class ProtectionType(models.Model, metaclass=TransMeta):
    name = models.CharField(_("name"), max_length=256)
    description = models.TextField(_("description"), blank=True, null=True)
    ordering = models.IntegerField(_("ordering"), default=10)
    color_class = models.CharField(
        max_length=30, default="text-primary", choices=COLOR_CLASS_CHOICES
    )
    icon_class = models.CharField(
        _("FA Icon Class"),
        choices=PROTECTION_FA_ICON_CLASS_CHOICES,
        max_length=50,
        default="fas fa-shield-alt",
    )

    class Meta:
        translate = ("name", "description")
        ordering = ("-ordering",)

    def __str__(self):
        return self.name


class RiotGearTypeQuerySet(HomebrewQuerySet):
    def for_extensions(self, extension_qs):
        return self.filter(
            Q(riotgear__extensions__id__in=extension_qs.all())
            | Q(
                riotgear__extensions__id__in=Extension.objects.filter(is_mandatory=True)
            )
        ).distinct()


class RiotGearType(SearchableCardListMixin, models.Model, metaclass=TransMeta):
    objects = RiotGearTypeQuerySet.as_manager()

    name = models.CharField(_("name"), max_length=256)
    is_shield = models.BooleanField(_("is shield"), default=False)
    description = models.TextField(_("description"), blank=True, null=True)
    ordering = models.IntegerField(_("ordering"), default=10)

    class Meta:
        ordering = ("-ordering",)
        translate = "name", "description"

    def __str__(self):
        return self.name

    def child_item_qs(self):
        return self.riotgear_set.all()


class RiotGearQuerySet(ExtensionSelectQuerySet, HomebrewQuerySet):
    pass


class RiotGear(HomebrewModel, metaclass=TransMeta):
    objects = RiotGearQuerySet.as_manager()

    extensions = models.ManyToManyField("rules.Extension", blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("created by"),
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    modified_at = models.DateTimeField(_("modified at"), auto_now=True)

    name = models.CharField(_("name"), max_length=256)
    description = models.TextField(_("description"), blank=True, null=True)
    type = models.ForeignKey(
        RiotGearType, verbose_name=_("type"), on_delete=models.CASCADE
    )

    shield_cover = models.IntegerField(_("shield cover"), default=0)
    encumbrance = models.IntegerField(_("encumbrance"), default=1)

    concealment = models.IntegerField(_("concealment"), default=0)
    weight = models.DecimalField(_("weight"), decimal_places=2, max_digits=6)
    price = models.DecimalField(_("price"), decimal_places=2, max_digits=8)

    class Meta:
        translate = ("name", "description")
        verbose_name = _("riot gear")
        verbose_name_plural = _("riot gear")

    def __str__(self):
        return self.name

    def get_protection(self):
        return self.riotgearprotection_set.order_by("protection_type__ordering")


class RiotGearProtection(models.Model):
    riot_gear = models.ForeignKey(RiotGear, on_delete=models.CASCADE)
    protection_type = models.ForeignKey(ProtectionType, on_delete=models.CASCADE)
    value = models.IntegerField(_("value"), default=1)

    class Meta:
        verbose_name = _("riot gear protection")
        verbose_name_plural = _("riot gear protections")

    def __str__(self):
        return self.protection_type.name


class CurrencyMap(models.Model):
    name = models.CharField(_("name"), max_length=20)

    def __str__(self):
        return self.name


class CurrencyMapUnit(models.Model, metaclass=TransMeta):
    currency_map = models.ForeignKey(CurrencyMap, on_delete=models.CASCADE)
    name = models.CharField(_("name"), max_length=20)

    value = models.DecimalField(
        _("value"),
        max_digits=6,
        decimal_places=2,
        default=1,
        help_text=_("Value in relation to the common unit."),
    )

    color_class = models.CharField(
        max_length=30, default="text-warning", choices=COLOR_CLASS_CHOICES
    )
    fa_icon_class = models.CharField(
        _("FA Icon Class"),
        choices=CURRENCY_FA_ICON_CLASS_CHOICES,
        max_length=30,
        default="fas fa-coins",
    )
    is_common = models.BooleanField(
        _("is common"),
        help_text=_("Is this the common unit people pay with?"),
        default=False,
    )
    ordering = models.IntegerField(_("ordering"), default=10)

    class Meta:
        translate = ("name",)
        get_latest_by = ("id",)
        ordering = ("-ordering",)

    def __str__(self):
        return self.name
