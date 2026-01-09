import hashlib
import os
import uuid

from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.db import models, transaction
from django.apps import apps
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from sorl.thumbnail import get_thumbnail

from characters.utils import static_thumbnail
from phasesix.models import ModelWithImage, image_upload_path
from rules.models import Extension
from worlds.unique_slugify import unique_slugify


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


class CampaignQuerySet(models.QuerySet):
    def for_world(self, world):
        if world is not None:
            return self.filter(world_extension=world.extension)
        return self.all()


class Campaign(ModelWithImage):
    VISIBILITY_CHOICES = (
        ("G", _("GM Only")),
        ("A", _("All")),
    )

    objects = CampaignQuerySet.as_manager()
    image_upload_to = "campaign_images"
    image = models.ImageField(
        _("image"),
        upload_to=image_upload_path,
        max_length=256,
        blank=True,
        null=True,
    )

    slug = models.SlugField(_("slug"), max_length=220)
    name = models.CharField(_("name"), max_length=80)
    ingame_act_date = models.CharField(
        _("in game act date"), max_length=40, blank=True, null=True
    )

    may_appear_on_start_page = models.BooleanField(
        _("may appear on start page"),
        help_text=_(
            "This campaign may appear on the anonymous start page (i.E. if it has only free images"
        ),
        default=False,
    )

    backdrop_image = models.ImageField(
        _("backdrop image"),
        upload_to="campaign_backdrop_images",
        max_length=256,
        blank=True,
        null=True,
    )
    backdrop_copyright = models.CharField(
        _("image copyright"), max_length=40, blank=True, null=True
    )
    backdrop_copyright_url = models.CharField(
        _("image copyright url"), max_length=150, blank=True, null=True
    )
    abstract = models.TextField(_("abstract"), blank=True, null=True)

    created_by = models.ForeignKey(
        "auth.User", verbose_name=_("created by"), on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    is_favorite = models.BooleanField(_("is favorite"), default=False)

    cloned_from = models.ForeignKey(
        "self",
        verbose_name=_("cloned from"),
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
    )

    epoch_extension = models.ForeignKey(
        "rules.Extension",
        limit_choices_to={"type": "e", "is_mandatory": False},
        on_delete=models.CASCADE,
        related_name="campaign_epoch_set",
        verbose_name=_("Epoch"),
    )
    world_extension = models.ForeignKey(
        "rules.Extension",
        limit_choices_to={"type": "w", "is_mandatory": False},
        on_delete=models.CASCADE,
        related_name="campaign_world_set",
        verbose_name=_("World"),
    )
    extensions = models.ManyToManyField(
        "rules.Extension",
        limit_choices_to={"is_mandatory": False, "type": "x"},
        blank=True,
    )
    forbidden_templates = models.ManyToManyField("rules.Template", blank=True)
    starting_template_points = models.IntegerField(
        _("additional starting career points"), default=0
    )

    # Integrations
    roll_on_site = models.BooleanField(
        _("roll on site"),
        help_text=_("Shows dice results on this platform."),
        default=True,
    )
    discord_integration = models.BooleanField(
        _("discord integration"),
        help_text=_("Enables the integration with discord. Requires a webhook url."),
        default=False,
    )
    tale_spire_integration = models.BooleanField(
        _("tale spire integration"),
        help_text=_(
            "Enables TaleSpire integration. All roll links are generated so that the TaleSpire game is accessed."
        ),
        default=False,
    )
    discord_webhook_url = models.URLField(
        _("discord webhook url"),
        max_length=256,
        help_text=_(
            "Create a discord webhook and paste it's url here to display dice results."
        ),
        blank=True,
        null=True,
    )

    currency_map = models.ForeignKey("armory.CurrencyMap", on_delete=models.CASCADE)
    seed_money = models.IntegerField(_("seed money"), default=2000)

    foe_visibility = models.CharField(
        _("foe visibility"), max_length=1, default="A", choices=VISIBILITY_CHOICES
    )

    npc_visibility = models.CharField(
        _("npc visibility"), max_length=1, default="A", choices=VISIBILITY_CHOICES
    )

    game_log_visibility = models.CharField(
        _("game log visibility"), max_length=1, default="A", choices=VISIBILITY_CHOICES
    )

    character_visibility = models.CharField(
        _("character visibility"), max_length=1, default="A", choices=VISIBILITY_CHOICES
    )

    class Meta:
        verbose_name = _("Campaign")
        verbose_name_plural = _("Campaigns")
        ordering = (
            "-is_favorite",
            "-created_at",
        )

    def save(self, **kwargs):
        if not self.slug:
            unique_slugify(self, str(self.name))
        super().save(**kwargs)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("campaigns:detail", kwargs={"slug": self.slug})

    def may_edit(self, user):
        if self.created_by == user:
            return True
        return False

    @property
    def extension_string(self):
        return ", ".join([e.name for e in self.extensions.all()])

    @property
    def campaign_hash(self):
        return hashlib.sha256(
            "{}{}{}{}".format(
                self.id, self.created_at, self.name, self.created_by.id
            ).encode("utf-8")
        ).hexdigest()

    @property
    def invite_link(self):
        return settings.BASE_URL + reverse(
            "campaigns:detail", kwargs={"slug": self.slug, "hash": self.campaign_hash}
        )

    def get_image_url(self, geometry="180", crop="center"):
        if self.image:
            return get_thumbnail(self.image, geometry, crop=crop, quality=99).url

        return static_thumbnail(
            f"img/silhouette.png",
            geometry_string=geometry,
            crop=crop,
        )

    def get_backdrop_image_url(self, geometry="600x160", crop="center"):
        image = self.epoch_extension.image
        if self.world_extension.image:
            image = self.world_extension.image
        if self.backdrop_image:
            image = self.backdrop_image

        return get_thumbnail(image, geometry, crop=crop, quality=99).url

    def clone(self):
        with transaction.atomic():
            clone = Campaign(
                name=self.name,
                ingame_act_date=self.ingame_act_date,
                image=_copy_field_file(self.image),
                image_copyright=self.image_copyright,
                image_copyright_url=self.image_copyright_url,
                may_appear_on_start_page=self.may_appear_on_start_page,
                backdrop_image=_copy_field_file(self.backdrop_image),
                backdrop_copyright=self.backdrop_copyright,
                backdrop_copyright_url=self.backdrop_copyright_url,
                abstract=self.abstract,
                created_by=self.created_by,
                is_favorite=self.is_favorite,
                epoch_extension=self.epoch_extension,
                world_extension=self.world_extension,
                starting_template_points=self.starting_template_points,
                roll_on_site=self.roll_on_site,
                discord_integration=self.discord_integration,
                tale_spire_integration=self.tale_spire_integration,
                discord_webhook_url=self.discord_webhook_url,
                currency_map=self.currency_map,
                seed_money=self.seed_money,
                foe_visibility=self.foe_visibility,
                npc_visibility=self.npc_visibility,
                game_log_visibility=self.game_log_visibility,
                character_visibility=self.character_visibility,
                cloned_from=self,
            )
            clone.slug = None
            clone.save()

            clone.extensions.set(self.extensions.all())
            clone.forbidden_templates.set(self.forbidden_templates.all())

            for cf in self.campaignfoe_set.all():
                CampaignFoe.objects.create(campaign=clone, foe=cf.foe, health=cf.health)

            for cr in self.campaignrecipe_set.all():
                CampaignRecipe.objects.create(campaign=clone, recipe=cr.recipe)

            Character = apps.get_model("characters", "Character")
            npc_map = {}
            for npc in Character.objects.filter(npc_campaign=self):
                new_npc = npc.clone(new_npc_campaign=clone)
                npc_map[npc.id] = new_npc

            for scene in self.scene_set.all():
                new_scene = Scene.objects.create(
                    campaign=clone, name=scene.name, text=scene.text
                )
                # Attach cloned NPCs only
                for npc in scene.npc.all():
                    if npc.id in npc_map:
                        new_scene.npc.add(npc_map[npc.id])

                # Clone handouts
                for handout in scene.handout_set.all():
                    Handout.objects.create(
                        scene=new_scene,
                        name=handout.name,
                        image=_copy_field_file(handout.image),
                        image_copyright=handout.image_copyright,
                        image_copyright_url=handout.image_copyright_url,
                    )

            Plot = apps.get_model("plots", "Plot")
            plot = Plot.objects.filter(campaign=self).first()
            if plot:
                plot.clone(campaign=clone, npc_map=npc_map)

            return clone

    @property
    def ws_room_name(self) -> str:
        """Websocket room name"""
        return f"campaign-{self.id}"


class CampaignFoe(models.Model):
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE)
    foe = models.ForeignKey("rules.Foe", on_delete=models.CASCADE)
    health = models.IntegerField(_("health"), default=6)

    def may_edit(self, user):
        return self.campaign.may_edit(user)


class CampaignRecipe(models.Model):
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE)
    recipe = models.ForeignKey("potions.Recipe", on_delete=models.CASCADE)

    def may_edit(self, user):
        return self.campaign.may_edit(user)


class Scene(models.Model):
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE)
    name = models.CharField(_("name"), max_length=80)
    text = models.TextField(_("text"), blank=True, null=True)

    npc = models.ManyToManyField("characters.Character")


class Handout(ModelWithImage):
    scene = models.ForeignKey(Scene, on_delete=models.CASCADE)
    image_upload_to = "campaign_handouts"
    image = models.ImageField(
        _("image"),
        upload_to=image_upload_path,
        max_length=256,
        blank=True,
        null=True,
    )
    name = models.CharField(_("name"), max_length=80)


class Roll(models.Model):
    campaign = models.ForeignKey(
        Campaign, blank=True, null=True, on_delete=models.CASCADE
    )
    character = models.ForeignKey(
        "characters.Character", blank=True, null=True, on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    header = models.CharField(_("header"), max_length=120, blank=True, null=True)
    description = models.TextField(_("description"), blank=True, null=True)
    roll_string = models.CharField(
        _("roll string"), max_length=20, blank=True, null=True
    )
    results_csv = models.CharField(_("results_csv"), max_length=120)

    modifier = models.IntegerField(_("modifier"), default=0)
    minimum_roll = models.IntegerField(_("minimum roll"), default=5)

    # statistics
    crit_count = models.IntegerField(_("crit count"), default=0)
    crit_sum = models.IntegerField(_("crit sum"), default=0)
    exploded_dice_count = models.IntegerField(_("exploded dice count"), default=0)
    exploded_dice_sum = models.IntegerField(_("exploded dice sum"), default=0)
    highest_single_roll = models.IntegerField(_("highest single roll"), default=0)
    successes_count = models.IntegerField(_("successes count"), default=0)
    successes_sum = models.IntegerField(_("successes sum"), default=0)
    fails_count = models.IntegerField(_("fails count"), default=0)
    fails_sum = models.IntegerField(_("fails sum"), default=0)
    total_sum = models.IntegerField(_("total sum"), default=0)

    class Meta:
        ordering = ("-created_at",)

    def save(self, *args, **kwargs):
        dice_list = [int(v) for v in self.results_csv.strip().split(",") if v]
        successes = [v for v in dice_list if v >= self.minimum_roll]
        fails = [v for v in dice_list if v < self.minimum_roll]
        exploded = [v for v in dice_list if v >= 6]
        crits = [v for v in dice_list if v >= 11]

        self.crit_count = len(crits)
        self.crit_sum = sum(crits)
        self.exploded_dice_count = len(exploded)
        self.exploded_dice_sum = sum(exploded)
        self.highest_single_roll = max(dice_list, default=0)
        self.successes_count = len(successes)
        self.successes_sum = sum(successes)
        self.fails_count = len(fails)
        self.fails_sum = sum(fails)
        self.total_sum = sum(dice_list) + self.modifier
        super().save(*args, **kwargs)

    def __str__(self):
        return self.header

    def get_sum(self):
        return sum(self.get_dice_list()) + self.modifier

    def get_dice_list(self):
        return [int(v) for v in self.results_csv.strip().split(",") if v]
