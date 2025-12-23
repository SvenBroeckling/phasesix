from django.db import models
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from sorl.thumbnail import get_thumbnail
from transmeta import TransMeta

from characters.utils import static_thumbnail
from homebrew.models import HomebrewModel, HomebrewQuerySet
from phasesix.models import ModelWithImage, PhaseSixModel
from rules.models import Extension, ModifierBase
from armory.models import Weapon, Item


class VehicleTypeQuerySet(HomebrewQuerySet):
    def for_extensions(self, extensions):
        """Filter vehicle types by extensions"""
        if not extensions:
            return self.none()
        return self.filter(extensions__in=extensions).distinct()


class VehicleType(HomebrewModel, PhaseSixModel, metaclass=TransMeta):
    """Vehicle type categorizes vehicles (Car, Motorcycle, Tank, Spaceship)"""

    objects = VehicleTypeQuerySet.as_manager()

    name = models.CharField(_("name"), max_length=100)
    description = models.TextField(_("description"), blank=True, null=True)
    is_flying = models.BooleanField(_("is flying"), default=False)
    is_water = models.BooleanField(_("is water"), default=False)
    is_space = models.BooleanField(_("is space"), default=False)

    extensions = models.ManyToManyField(
        "rules.Extension",
        blank=True,
        related_name="vehicle_types",
        verbose_name=_("extensions"),
    )
    class Meta:
        translate = ("name", "description")
        verbose_name = _("vehicle type")
        verbose_name_plural = _("vehicle types")

    def __str__(self):
        return self.name

    def child_item_qs(self):
        return self.vehicle_set.all()


class MountPoint(HomebrewModel, metaclass=TransMeta):
    """Defines a mounting point on a vehicle where machinery or weapons can be installed"""

    name = models.CharField(_("name"), max_length=100)
    description = models.TextField(_("description"), blank=True, null=True)

    TYPE_CHOICES = (
        ("weapon", _("Weapon Mount")),
        ("equipment", _("Equipment Mount")),
        ("armor", _("Armor Mount")),
        ("engine", _("Engine Mount")),
        ("special", _("Special Mount")),
    )
    mount_type = models.CharField(
        _("mount type"), max_length=20, choices=TYPE_CHOICES, default="weapon"
    )

    SIZE_CHOICES = (
        ("tiny", _("Tiny")),
        ("small", _("Small")),
        ("medium", _("Medium")),
        ("large", _("Large")),
        ("huge", _("Huge")),
    )
    size = models.CharField(
        _("size"), max_length=10, choices=SIZE_CHOICES, default="medium"
    )

    DIRECTION_CHOICES = (
        ("front", _("Front")),
        ("rear", _("Rear")),
        ("left", _("Left")),
        ("right", _("Right")),
        ("top", _("Top")),
        ("bottom", _("Bottom")),
        ("turret", _("Turret (360°)")),
    )
    direction = models.CharField(
        _("direction"), max_length=10, choices=DIRECTION_CHOICES, default="front"
    )

    extensions = models.ManyToManyField(
        "rules.Extension",
        blank=True,
        related_name="mount_points",
        verbose_name=_("extensions"),
    )

    class Meta:
        translate = ("name", "description")
        verbose_name = _("mount point")
        verbose_name_plural = _("mount points")

    def __str__(self):
        return f"{self.name} ({self.get_mount_type_display()}, {self.get_size_display()}, {self.get_direction_display()})"


class VehicleMachinery(HomebrewModel, ModelWithImage, PhaseSixModel, metaclass=TransMeta):
    """Represents equipment, weapons, or systems that can be mounted on a vehicle"""

    image_upload_to = "vehicle_machinery_images"
    name = models.CharField(_("name"), max_length=100)
    description = models.TextField(_("description"), blank=True, null=True)

    weapon = models.ForeignKey(
        "armory.Weapon",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name=_("weapon"),
        related_name="vehicle_machinery",
    )

    item = models.ForeignKey(
        "armory.Item",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name=_("item"),
        related_name="vehicle_machinery",
    )

    weight = models.FloatField(_("weight"), default=0)
    price = models.IntegerField(_("price"), default=0)

    required_mount_type = models.CharField(
        _("required mount type"), max_length=20, choices=MountPoint.TYPE_CHOICES
    )
    required_mount_size = models.CharField(
        _("required mount size"), max_length=10, choices=MountPoint.SIZE_CHOICES
    )

    power_consumption = models.IntegerField(
        _("power consumption"), default=0, help_text=_("Energy units required")
    )

    extensions = models.ManyToManyField(
        "rules.Extension",
        blank=True,
        related_name="vehicle_machinery",
        verbose_name=_("extensions"),
    )

    class Meta:
        translate = ("name", "description")
        verbose_name = _("vehicle machinery")
        verbose_name_plural = _("vehicle machinery")

    def __str__(self):
        return self.name

    def get_image_url(self, geometry="180", crop="center"):
        """Get image URL with thumbnailing"""
        if self.image:
            return get_thumbnail(self.image, geometry, crop=crop, quality=99).url

        return static_thumbnail(
            f"img/silhouette.png",
            geometry_string=geometry,
            crop=crop,
        )


class FuelType(models.Model, metaclass=TransMeta):
    """Different types of fuel or power sources for vehicles"""

    name = models.CharField(_("name"), max_length=100)
    description = models.TextField(_("description"), blank=True, null=True)

    is_renewable = models.BooleanField(_("is renewable"), default=False)
    energy_density = models.IntegerField(_("energy density"), default=100)
    cost_per_unit = models.IntegerField(_("cost per unit"), default=1)

    extensions = models.ManyToManyField(
        "rules.Extension",
        blank=True,
        related_name="fuel_types",
        verbose_name=_("extensions"),
    )

    class Meta:
        translate = ("name", "description")
        verbose_name = _("fuel type")
        verbose_name_plural = _("fuel types")

    def __str__(self):
        return self.name


class VehicleQuerySet(HomebrewQuerySet):
    """Custom queryset for vehicles"""

    def for_world(self, world):
        if world is None:
            return self.all()

        world_extensions = world.extension.id if world.extension else None
        if world_extensions:
            return self.filter(extensions__id=world_extensions).distinct()
        return self.none()


class Vehicle(HomebrewModel, ModelWithImage, PhaseSixModel, metaclass=TransMeta):
    """Main vehicle model"""

    objects = VehicleQuerySet.as_manager()
    image_upload_to = "vehicle_images"

    name = models.CharField(_("name"), max_length=100)
    description = models.TextField(_("description"), blank=True, null=True)
    vehicle_type = models.ForeignKey(
        "vehicles.VehicleType",
        on_delete=models.CASCADE,
        verbose_name=_("vehicle type"),
    )

    crew_required = models.IntegerField(
        _("crew required"),
        default=1,
        help_text=_("Minimum number of crew needed to operate"),
    )
    passenger_capacity = models.IntegerField(_("passenger capacity"), default=0)
    cargo_capacity = models.FloatField(
        _("cargo capacity"), default=0, help_text=_("Cargo capacity in kg")
    )

    max_speed = models.IntegerField(
        _("maximum speed"), default=0, help_text=_("Maximum speed in km/h")
    )
    acceleration = models.FloatField(
        _("acceleration"), default=0, help_text=_("Acceleration rate")
    )
    handling = models.IntegerField(
        _("handling"), default=0, help_text=_("Handling rating")
    )
    durability = models.IntegerField(
        _("durability"), default=10, help_text=_("Vehicle health points")
    )
    armor = models.IntegerField(_("armor"), default=0, help_text=_("Damage reduction"))

    fuel_type = models.ForeignKey(
        "vehicles.FuelType",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("fuel type"),
    )
    fuel_capacity = models.FloatField(_("fuel capacity"), default=0)
    fuel_efficiency = models.FloatField(
        _("fuel efficiency"), default=0, help_text=_("Distance per unit of fuel")
    )
    range = models.IntegerField(
        _("range"), default=0, help_text=_("Maximum range in km")
    )

    energy_capacity = models.IntegerField(
        _("energy capacity"), default=0, help_text=_("Energy storage capacity")
    )
    power_output = models.IntegerField(
        _("power output"), default=0, help_text=_("Power generated")
    )

    length = models.FloatField(_("length"), default=0, help_text=_("Length in meters"))
    width = models.FloatField(_("width"), default=0, help_text=_("Width in meters"))
    height = models.FloatField(_("height"), default=0, help_text=_("Height in meters"))
    weight = models.FloatField(_("weight"), default=0, help_text=_("Weight in kg"))

    evasion = models.IntegerField(
        _("evasion"), default=0, help_text=_("Ability to avoid attacks")
    )
    stealth = models.IntegerField(
        _("stealth"), default=0, help_text=_("Stealth rating")
    )

    mount_points = models.ManyToManyField(
        "vehicles.MountPoint",
        through="VehicleMountPoint",
        verbose_name=_("mount points"),
        related_name="vehicles",
    )

    RARITY_CHOICES = (
        ("common", _("Common")),
        ("uncommon", _("Uncommon")),
        ("rare", _("Rare")),
        ("very_rare", _("Very Rare")),
        ("legendary", _("Legendary")),
    )
    rarity = models.CharField(
        _("rarity"), max_length=10, choices=RARITY_CHOICES, default="common"
    )
    price = models.IntegerField(_("price"), default=0)

    extensions = models.ManyToManyField(
        "rules.Extension",
        blank=True,
        related_name="vehicles",
        verbose_name=_("extensions"),
    )

    TECH_LEVEL_CHOICES = (
        (1, _("Primitive")),
        (2, _("Basic")),
        (3, _("Advanced")),
        (4, _("Futuristic")),
        (5, _("Cutting-Edge")),
        (6, _("Alien/Otherworldly")),
    )
    tech_level = models.IntegerField(
        _("tech level"), choices=TECH_LEVEL_CHOICES, default=2
    )

    class Meta:
        translate = ("name", "description")
        verbose_name = _("vehicle")
        verbose_name_plural = _("vehicles")

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("vehicles:detail", args=[self.id])

    def get_image_url(self, geometry="180", crop="center"):
        """Get image URL with thumbnailing"""
        if self.image:
            return get_thumbnail(self.image, geometry, crop=crop, quality=99).url

        return static_thumbnail(
            f"img/silhouette.png",
            geometry_string=geometry,
            crop=crop,
        )

    def get_mounted_weapons(self):
        """Return all weapons mounted on this vehicle"""
        return self.vehiclemountpoint_set.filter(
            mounted_machinery__isnull=False, mounted_machinery__weapon__isnull=False
        )

    def get_mounted_equipment(self):
        """Return all equipment mounted on this vehicle"""
        return self.vehiclemountpoint_set.filter(
            mounted_machinery__isnull=False, mounted_machinery__item__isnull=False
        )

    def total_power_consumption(self):
        """Calculate total power consumed by all mounted machinery"""
        total = 0
        for mount in self.vehiclemountpoint_set.filter(mounted_machinery__isnull=False):
            if mount.mounted_machinery:
                total += mount.mounted_machinery.power_consumption
        return total

    def remaining_power(self):
        """Calculate remaining power available"""
        return self.power_output - self.total_power_consumption()

    def is_operational(self):
        """Check if vehicle has enough power to operate"""
        return self.remaining_power() >= 0

    def calculate_range(self):
        """Calculate actual range based on fuel efficiency and capacity"""
        if self.fuel_efficiency and self.fuel_capacity:
            return self.fuel_efficiency * self.fuel_capacity
        return self.range


class VehicleMountPoint(models.Model):
    """Through model to connect vehicles with mount points and installed machinery"""

    vehicle = models.ForeignKey("vehicles.Vehicle", on_delete=models.CASCADE)
    mount_point = models.ForeignKey("vehicles.MountPoint", on_delete=models.CASCADE)

    mounted_machinery = models.ForeignKey(
        "vehicles.VehicleMachinery",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("mounted machinery"),
    )

    custom_name = models.CharField(
        _("custom name"), max_length=100, blank=True, null=True
    )

    is_operational = models.BooleanField(_("is operational"), default=True)
    damage_level = models.IntegerField(_("damage level"), default=0)

    class Meta:
        verbose_name = _("vehicle mount point")
        verbose_name_plural = _("vehicle mount points")
        unique_together = ("vehicle", "mount_point")

    def __str__(self):
        if self.custom_name:
            return f"{self.custom_name} on {self.vehicle.name}"
        return f"{self.mount_point.name} on {self.vehicle.name}"

    def is_compatible(self):
        """Check if the mounted machinery is compatible with this mount point"""
        if not self.mounted_machinery:
            return True

        return (
            self.mounted_machinery.required_mount_type == self.mount_point.mount_type
            and self.mounted_machinery.required_mount_size == self.mount_point.size
        )


class VehicleStatusEffect(models.Model, metaclass=TransMeta):
    """Status effects that can be applied to vehicles (damaged, emp, etc.)"""

    name = models.CharField(_("name"), max_length=100)
    description = models.TextField(_("description"), blank=True, null=True)

    speed_modifier = models.IntegerField(_("speed modifier"), default=0)
    handling_modifier = models.IntegerField(_("handling modifier"), default=0)
    armor_modifier = models.IntegerField(_("armor modifier"), default=0)
    power_modifier = models.IntegerField(_("power modifier"), default=0)
    evasion_modifier = models.IntegerField(_("evasion modifier"), default=0)

    duration = models.IntegerField(
        _("duration"), default=1, help_text=_("Duration in rounds, -1 for permanent")
    )

    is_positive = models.BooleanField(_("is positive"), default=False)

    class Meta:
        translate = ("name", "description")
        verbose_name = _("vehicle status effect")
        verbose_name_plural = _("vehicle status effects")

    def __str__(self):
        return self.name


class ActiveVehicleStatusEffect(models.Model):
    """Instance of a status effect currently affecting a vehicle"""

    vehicle = models.ForeignKey(
        "vehicles.Vehicle",
        on_delete=models.CASCADE,
        related_name="active_status_effects",
    )
    status_effect = models.ForeignKey(
        "vehicles.VehicleStatusEffect",
        on_delete=models.CASCADE,
    )

    remaining_duration = models.IntegerField(_("remaining duration"), default=1)
    applied_at = models.DateTimeField(_("applied at"), auto_now_add=True)
    applied_by = models.ForeignKey(
        "characters.Character",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="vehicle_effects_applied",
    )

    class Meta:
        verbose_name = _("active vehicle status effect")
        verbose_name_plural = _("active vehicle status effects")

    def __str__(self):
        return f"{self.status_effect.name} on {self.vehicle.name}"

    def is_expired(self):
        """Check if this effect has expired"""
        return self.status_effect.duration > 0 and self.remaining_duration <= 0
