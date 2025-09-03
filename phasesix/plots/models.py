from django.utils.translation import gettext as _
from django.db import models
from transmeta import TransMeta


class Plot(models.Model, metaclass=TransMeta):
    name = models.CharField(_("name"), max_length=128)
    player_abstract = models.TextField(_("abstract for players"))
    gm_description = models.TextField(_("gm description"))
    image = models.ImageField(
        _("image"), upload_to="plot_images", blank=True, null=True
    )
    epoch_extension = models.ForeignKey(
        "rules.Extension",
        limit_choices_to={"type": "e", "is_mandatory": False},
        on_delete=models.CASCADE,
        related_name="plot_epoch_set",
        verbose_name=_("Epoch"),
    )
    world_extension = models.ForeignKey(
        "rules.Extension",
        limit_choices_to={"type": "w", "is_mandatory": False},
        on_delete=models.CASCADE,
        related_name="plot_world_set",
        verbose_name=_("World"),
    )
    extensions = models.ManyToManyField(
        "rules.Extension",
        limit_choices_to={"is_mandatory": False, "type": "x"},
        blank=True,
    )

    def __str__(self):
        return self.name


class Location(models.Model, metaclass=TransMeta):
    name = models.CharField(_("name"), max_length=128)
    description = models.TextField(_("description"))
    image = models.ImageField(
        _("image"), upload_to="plot_location_images", blank=True, null=True
    )

    def __str__(self):
        return self.name


class Handout(models.Model, metaclass=TransMeta):
    name = models.CharField(_("name"), max_length=128)
    description = models.TextField(_("description"))
    image = models.ImageField(
        _("image"), upload_to="plot_handout_images", blank=True, null=True
    )

    def __str__(self):
        return self.name


class PlotElement(models.Model, metaclass=TransMeta):
    class ElementType(models.TextChoices):
        ROOT = "r", _("Plot Root")
        ACT = "a", _("Act")
        SCENE = "s", _("Scene")
        ENCOUNTER = "e", _("Encounter")

    plot = models.ForeignKey(Plot, verbose_name=_("Plot"), on_delete=models.CASCADE)
    parent = models.ForeignKey(
        "self", on_delete=models.CASCADE, related_name="children", null=True, blank=True
    )

    name = models.CharField(_("name"), max_length=128)
    type = models.CharField(
        _("type"), max_length=1, choices=ElementType.choices, default="s"
    )

    gm_notes = models.TextField(_("GM notes"), blank=True, null=True)
    player_summary = models.TextField(_("player summary"), blank=True, null=True)

    npc = models.ManyToManyField("characters.Character")
    handouts = models.ManyToManyField(Handout)
    locations = models.ManyToManyField(Location)

    def __str__(self):
        return self.name
