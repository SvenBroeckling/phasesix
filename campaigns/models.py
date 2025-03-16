import hashlib

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from sorl.thumbnail import get_thumbnail

from characters.utils import static_thumbnail
from rules.models import Extension


class CampaignQuerySet(models.QuerySet):
    def for_world_configuration(self, world_configuration):
        if world_configuration is not None:
            return self.filter(world=world_configuration.world.extension)
        return self.all()


class Campaign(models.Model):
    VISIBILITY_CHOICES = (
        ("G", _("GM Only")),
        ("A", _("All")),
    )

    objects = CampaignQuerySet.as_manager()

    name = models.CharField(_("name"), max_length=80)
    image = models.ImageField(
        _("image"), upload_to="campaign_images", max_length=200, blank=True, null=True
    )
    image_copyright = models.CharField(
        _("image copyright"), max_length=40, blank=True, null=True
    )
    image_copyright_url = models.CharField(
        _("image copyright url"), max_length=150, blank=True, null=True
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
        max_length=200,
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

    epoch = models.ForeignKey(
        "rules.Extension",
        limit_choices_to={"type": "e", "is_mandatory": False},
        on_delete=models.CASCADE,
        related_name="campaign_epoch_set",
        verbose_name=_("Epoch"),
    )
    world = models.ForeignKey(
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
        ordering = ("-created_at",)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("campaigns:detail", kwargs={"pk": self.id})

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
            "campaigns:detail", kwargs={"pk": self.id, "hash": self.campaign_hash}
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
        image = self.epoch.image
        if self.world.image:
            image = self.world.image
        if self.backdrop_image:
            image = self.backdrop_image

        return get_thumbnail(image, geometry, crop=crop, quality=99).url

    @property
    def ws_room_name(self) -> str:
        """Websocket room name"""
        return f"campaign-{self.id}"


class Foe(models.Model):
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE)
    wiki_page = models.ForeignKey("worlds.WikiPage", on_delete=models.CASCADE)

    def may_edit(self, user):
        return self.campaign.may_edit(user)


class Scene(models.Model):
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE)
    name = models.CharField(_("name"), max_length=80)
    text = models.TextField(_("text"), blank=True, null=True)

    npc = models.ManyToManyField("characters.Character")


class Handout(models.Model):
    scene = models.ForeignKey(Scene, on_delete=models.CASCADE)
    name = models.CharField(_("name"), max_length=80)
    image = models.ImageField(
        _("image"), upload_to="campaign_handouts", max_length=200, blank=True, null=True
    )
    image_copyright = models.CharField(
        _("image copyright"), max_length=40, blank=True, null=True
    )
    image_copyright_url = models.CharField(
        _("image copyright url"), max_length=150, blank=True, null=True
    )


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
