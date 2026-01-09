from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.db import models, transaction
from django.utils.translation import gettext as _
from transmeta import TransMeta
import os
import uuid

from homebrew.models import HomebrewModel
from phasesix.models import ModelWithImage, PhaseSixModel


def _copy_field_file(field_file):
    """Return a saved copy of the given FieldFile (or None if empty)."""
    if not field_file:
        return None

    field_file.open("rb")
    try:
        file_data = field_file.read()
    finally:
        field_file.close()

    base_dir, filename = os.path.split(field_file.name)
    name, ext = os.path.splitext(filename)
    new_filename = f"{name}_{uuid.uuid4().hex}{ext}"
    new_path = os.path.join(base_dir, new_filename)

    return default_storage.save(new_path, ContentFile(file_data))


class Plot(HomebrewModel, ModelWithImage, PhaseSixModel, metaclass=TransMeta):
    name = models.CharField(_("name"), max_length=128)
    language = models.CharField(
        _("language"), max_length=4, default="en", choices=settings.LANGUAGES
    )

    player_abstract = models.TextField(_("abstract for players"))
    gm_description = models.TextField(_("gm description"))
    image = models.ImageField(
        _("image"), upload_to="plot_images", blank=True, null=True, max_length=256
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
    cloned_from = models.ForeignKey(
        "self",
        verbose_name=_("cloned from"),
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )
    created_by = models.ForeignKey(
        "auth.User", verbose_name=_("created by"), on_delete=models.CASCADE
    )
    campaign = models.OneToOneField(
        "campaigns.Campaign",
        verbose_name=_("campaign"),
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("plot")
        verbose_name_plural = _("plots")

    @property
    def root_elements(self):
        return (
            self.plotelement_set.filter(parent__isnull=True)
            .prefetch_related("children")
            .order_by("ordering")
            .all()
        )

    def clone(self, campaign=None, npc_map=None):
        npc_map = npc_map or {}
        with transaction.atomic():
            clone = Plot.objects.create(
                name=self.name,
                language=self.language,
                player_abstract=self.player_abstract,
                gm_description=self.gm_description,
                image=_copy_field_file(self.image),
                epoch_extension=self.epoch_extension,
                world_extension=self.world_extension,
                cloned_from=self,
                created_by=self.created_by,
                campaign=campaign,
            )
            clone.extensions.set(self.extensions.all())

            elements = list(
                self.plotelement_set.all()
                .select_related("parent")
                .prefetch_related("handouts", "locations", "npc", "foes")
            )
            element_map = {}
            for element in elements:
                element_map[element.id] = PlotElement.objects.create(
                    plot=clone,
                    parent=None,
                    name=element.name,
                    gm_notes=element.gm_notes,
                    player_summary=element.player_summary,
                    ordering=element.ordering,
                )

            for element in elements:
                if element.parent_id:
                    element_map[element.id].parent = element_map[element.parent_id]
                    element_map[element.id].save(update_fields=["parent"])

            handout_map = {}
            location_map = {}
            for element in elements:
                new_element = element_map[element.id]

                new_handouts = []
                for handout in element.handouts.all():
                    if handout.id not in handout_map:
                        handout_map[handout.id] = Handout.objects.create(
                            name=handout.name,
                            description=handout.description,
                            image=_copy_field_file(handout.image),
                        )
                    new_handouts.append(handout_map[handout.id])
                if new_handouts:
                    new_element.handouts.set(new_handouts)

                new_locations = []
                for location in element.locations.all():
                    if location.id not in location_map:
                        location_map[location.id] = Location.objects.create(
                            name=location.name,
                            description=location.description,
                            image=_copy_field_file(location.image),
                        )
                    new_locations.append(location_map[location.id])
                if new_locations:
                    new_element.locations.set(new_locations)

                new_npcs = []
                for npc in element.npc.all():
                    if npc.id not in npc_map:
                        npc_map[npc.id] = npc.clone(
                            plot=clone, new_npc_campaign=campaign
                        )
                    new_npcs.append(npc_map[npc.id])
                if new_npcs:
                    new_element.npc.set(new_npcs)

                if element.foes.exists():
                    new_element.foes.set(element.foes.all())

            return clone


class Location(models.Model, metaclass=TransMeta):
    name = models.CharField(_("name"), max_length=128)
    description = models.TextField(_("description"))
    image = models.ImageField(
        _("image"),
        upload_to="plot_location_images",
        blank=True,
        null=True,
        max_length=256,
    )

    def __str__(self):
        return self.name


class Handout(models.Model, metaclass=TransMeta):
    name = models.CharField(_("name"), max_length=128)
    description = models.TextField(_("description"))
    image = models.ImageField(
        _("image"),
        upload_to="plot_handout_images",
        blank=True,
        null=True,
        max_length=256,
    )

    def __str__(self):
        return self.name


class PlotElement(models.Model, metaclass=TransMeta):
    plot = models.ForeignKey(Plot, verbose_name=_("Plot"), on_delete=models.CASCADE)
    parent = models.ForeignKey(
        "self", on_delete=models.CASCADE, related_name="children", null=True, blank=True
    )

    name = models.CharField(_("name"), max_length=128)

    gm_notes = models.TextField(_("GM notes"), blank=True, null=True)
    player_summary = models.TextField(_("player summary"), blank=True, null=True)

    npc = models.ManyToManyField("characters.Character", blank=True)
    foes = models.ManyToManyField("rules.Foe", blank=True)
    handouts = models.ManyToManyField(Handout, blank=True)
    locations = models.ManyToManyField(Location, blank=True)
    ordering = models.PositiveIntegerField(_("ordering"), default=0)

    class Meta:
        ordering = ["ordering"]

    def __str__(self):
        return self.name
