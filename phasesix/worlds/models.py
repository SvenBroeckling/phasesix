import reversion
from django.conf import settings
from django.db import models
from django.templatetags.static import static
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from sorl.thumbnail import get_thumbnail
from transmeta import TransMeta

from characters.utils import static_thumbnail
from homebrew.models import HomebrewModel, HomebrewQuerySet
from worlds.unique_slugify import unique_slugify


class WorldSiteConfiguration(models.Model):
    world = models.ForeignKey("worlds.World", on_delete=models.CASCADE)
    dns_domain_name = models.CharField(
        _("dns domain name"),
        max_length=120,
        blank=True,
        null=True,
        help_text=_(
            "This world is set as default if the given dns domain name is requested"
        ),
    )
    session_cookie_domain = models.CharField(
        _("session cookie domain"), max_length=120, blank=True, null=True
    )

    class Meta:
        verbose_name = _("world site configuration")
        verbose_name_plural = _("world site configurations")


@reversion.register
class World(models.Model, metaclass=TransMeta):
    INDEX_TEMPLATE_CHOICES = (
        ("index.html", "index.html"),
        ("worlds/world_detail.html", "worlds/world_detail.html"),
    )
    SCSS_FILE_CHOICES = (
        ("theme/phasesix.scss", "theme/phasesix.scss"),
        ("theme/tirakan.scss", "theme/tirakan.scss"),
        ("theme/nexus.scss", "theme/nexus.scss"),
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("created by"),
    )

    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    modified_at = models.DateTimeField(_("modified at"), auto_now=True)

    name = models.CharField(_("name"), max_length=120)
    slug = models.SlugField(_("slug"), max_length=220, unique=True, null=True)
    brand_name = models.CharField(_("Brand name"), max_length=80)
    brand_claim = models.CharField(
        _("Brand claim"), max_length=80, null=True, blank=True
    )
    brand_logo = models.ImageField(
        _("Brand Logo"), max_length=256, null=True, blank=True, upload_to="brand_logos"
    )

    description_1 = models.TextField(_("description 1"), blank=True, null=True)
    description_2 = models.TextField(_("description 2"), blank=True, null=True)
    description_3 = models.TextField(_("description 3"), blank=True, null=True)

    is_active = models.BooleanField(_("is active"), default=True)
    is_default = models.BooleanField(_("is default"), default=False)
    extension = models.ForeignKey(
        "rules.Extension",
        verbose_name=_("extension"),
        help_text=_(
            "The corresponding world extension, which is added to the characters."
        ),
        limit_choices_to={"type": "w"},
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )

    show_in_worlds_overview = models.BooleanField(
        _("show in worlds overview"), default=False
    )

    image = models.ImageField(
        _("image"), upload_to="world_images", max_length=256, blank=True, null=True
    )
    image_copyright = models.CharField(
        _("image copyright"), max_length=40, blank=True, null=True
    )
    image_copyright_url = models.CharField(
        _("image copyright url"), max_length=150, blank=True, null=True
    )

    info_name_cm = models.CharField(
        _("Name for centimeter"), max_length=20, default="cm"
    )
    info_name_kg = models.CharField(_("Name for kilogram"), max_length=20, default="kg")
    foe_overview_wiki_page = models.ForeignKey(
        "worlds.WikiPage",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="foe_overview_world_set",
    )

    scss_file = models.CharField(
        _("SCSS File"),
        max_length=40,
        choices=SCSS_FILE_CHOICES,
        default="theme/phasesix.scss",
    )

    ordering = models.IntegerField(_("ordering"), default=100)

    class Meta:
        ordering = ("ordering",)
        translate = (
            "name",
            "description_1",
            "description_2",
            "description_3",
            "info_name_cm",
            "info_name_kg",
            "brand_name",
            "brand_claim",
        )
        verbose_name = _("world")
        verbose_name_plural = _("worlds")

    def __str__(self):
        return self.name

    def may_edit(self, user):
        return user.is_superuser or user == self.created_by

    def get_absolute_url(self):
        return reverse("worlds:detail", args=[self.slug])

    @property
    def world(self):
        """Used to unify the navigation"""
        return self

    def is_subpage_of(self, parent):
        """Used to unify the navigation"""
        return False

    def is_world(self):
        """Used to unify the navigation"""
        return True

    def get_backdrop_image_url(self, geometry="180", crop="center"):
        return self.get_image_url(geometry=geometry, crop=crop)

    def get_image_url(self, geometry="180", crop="center"):
        image = self.get_image()

        if image:
            return get_thumbnail(image["image"], geometry, crop=crop, quality=99).url

        return static_thumbnail(
            f"img/silhouette.png",
            geometry_string=geometry,
            crop=crop,
        )

    def get_image(self):
        if self.image:
            return {
                "image": self.image,
                "copyright": self.image_copyright,
                "copyright_url": self.image_copyright_url,
            }
        else:
            return None

    @property
    def identifier(self):
        return self.extension.identifier

    @property
    def scss_file_static(self):
        return static(self.scss_file)


class WorldLeadImage(models.Model):
    world = models.ForeignKey("worlds.World", on_delete=models.CASCADE)
    image = models.ImageField(_("image"), upload_to="world_lead_images", max_length=256)
    character = models.ForeignKey(
        "characters.Character",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("character"),
    )

    class Meta:
        verbose_name = _("world lead image")
        verbose_name_plural = _("world lead images")


class WikiPageQuerySet(models.QuerySet):
    def get_top_level(self):
        return self.filter(parent=None)


@reversion.register
class WikiPage(models.Model, metaclass=TransMeta):
    objects = WikiPageQuerySet.as_manager()
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("created by"),
    )

    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    modified_at = models.DateTimeField(_("modified at"), auto_now=True)

    name = models.CharField(_("name"), max_length=120)
    short_name = models.CharField(
        _("short name"),
        help_text=_("An optional short name for the default link text."),
        blank=True,
        null=True,
        max_length=90,
    )
    slug = models.SlugField(_("slug"), max_length=220, unique=True)
    world = models.ForeignKey(
        "worlds.World",
        verbose_name=_("world"),
        help_text=_("The world this page belongs to."),
        on_delete=models.CASCADE,
    )

    exclude_from_foe_search = models.BooleanField(
        _("excelude from foe search"), default=False
    )

    parent = models.ForeignKey(
        "self",
        verbose_name=_("parent"),
        help_text=_("The parent wiki page."),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )

    text = models.TextField(
        _("text"),
        help_text=_("The wiki page text. This may contain Wiki links."),
        blank=True,
        null=True,
    )

    image = models.ImageField(
        _("image"), upload_to="wiki_page_images", max_length=256, blank=True, null=True
    )
    image_copyright = models.CharField(
        _("image copyright"), max_length=40, blank=True, null=True
    )
    image_copyright_url = models.CharField(
        _("image copyright url"), max_length=150, blank=True, null=True
    )

    actions_heading = models.CharField(
        _("actions heading"), max_length=40, null=True, blank=True
    )
    is_active = models.BooleanField(_("is active"), default=True)
    ordering = models.IntegerField(_("ordering"), default=100)

    class Meta:
        ordering = ("ordering",)
        translate = ("name", "short_name", "text", "actions_heading")
        verbose_name = _("wiki page")
        verbose_name_plural = _("wiki pages")

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse(
            "worlds:wiki_page",
            kwargs={"world_slug": self.world.slug, "slug": self.slug},
        )

    def save(self, **kwargs):
        if not self.slug:
            unique_slugify(self, str(self.name_de))
        super().save(**kwargs)

    def may_edit(self, user):
        return user.is_superuser or user == self.created_by

    def get_wiki_link_text(self):
        if self.short_name:
            return self.short_name
        return self.name

    def may_be_added_to_campaign(self):
        if self.exclude_from_foe_search:
            return False
        if self.wikipagegameaction_set.exists():
            return True
        if self.wikipagegamevalues_set.exists():
            return True
        return False

    def get_image_url(self, geometry="180", crop="center"):
        image = self.get_image()

        if image:
            return get_thumbnail(image["image"], geometry, crop=crop, quality=99).url

        return static_thumbnail(
            f"img/silhouette.png",
            geometry_string=geometry,
            crop=crop,
        )

    def get_backdrop_image_url(self, geometry="1800x500", crop="center"):
        if self.image:
            return get_thumbnail(self.image, geometry, crop=crop, quality=99).url
        return None

    def get_image(self):
        if self.image:
            return {
                "image": self.image,
                "copyright": self.image_copyright,
                "copyright_url": self.image_copyright_url,
            }
        if self.parent and self.parent.image:
            return self.parent.get_image()

        return self.world.get_image()

    def is_subpage_of(self, parent):
        if self == parent:
            return True
        if self.parent == parent:
            return True
        if self.parent:
            return self.parent.is_subpage_of(parent)
        return False

    def has_values_or_actions(self):
        return (
            self.wikipagegamevalues_set.exists() or self.wikipagegameaction_set.exists()
        )


@reversion.register
class WikiPageImage(models.Model):
    wiki_page = models.ForeignKey(
        "worlds.WikiPage",
        verbose_name=_("wiki page"),
        help_text=_("The wiki page the image belongs to."),
        on_delete=models.CASCADE,
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("created by"),
    )

    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    modified_at = models.DateTimeField(_("modified at"), auto_now=True)

    image = models.ImageField(_("image"), max_length=256, upload_to="wiki_page_images")
    image_copyright = models.CharField(
        _("image copyright"), max_length=40, blank=True, null=True
    )
    image_copyright_url = models.CharField(
        _("image copyright url"), max_length=150, blank=True, null=True
    )

    caption = models.CharField(_("caption"), max_length=120)
    slug = models.SlugField(_("slug"), max_length=220, unique=True, null=True)

    class Meta:
        verbose_name = _("wiki page image")
        verbose_name_plural = _("wiki page images")

    def __str__(self):
        return self.caption

    def save(self, **kwargs):
        if not self.slug:
            unique_slugify(self, str(self.caption))
        super().save(**kwargs)

    def get_wiki_tag(self):
        return "{{%s|image-end}}" % self.slug

    def may_edit(self, user):
        return user.is_superuser or user == self.wiki_page.created_by

    def get_image(self):
        return {
            "image": self.image,
            "caption": self.caption,
        }


class WikiPageFoeType(models.Model, metaclass=TransMeta):
    name = models.CharField(_("name"), max_length=100)

    class Meta:
        translate = ("name",)
        verbose_name = _("wiki page foe type")
        verbose_name_plural = _("wiki page foe types")

    def __str__(self):
        return self.name


class WikiPageFoeResistanceOrWeakness(models.Model, metaclass=TransMeta):
    name = models.CharField(_("name"), max_length=100)

    class Meta:
        translate = ("name",)
        verbose_name = _("wiki page foe resistance or weakness")
        verbose_name_plural = _("wiki page foe resistances or weaknesses")

    def __str__(self):
        return self.name


@reversion.register
class WikiPageGameValues(models.Model):
    wiki_page = models.ForeignKey(
        "worlds.WikiPage",
        verbose_name=_("wiki page"),
        help_text=_("The wiki page the values belong to."),
        on_delete=models.CASCADE,
    )

    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    modified_at = models.DateTimeField(_("modified at"), auto_now=True)

    type = models.ForeignKey(
        WikiPageFoeType, verbose_name=_("type"), on_delete=models.CASCADE
    )

    health = models.IntegerField(_("health"), default=6)
    arcana = models.IntegerField(_("arcana"), default=0)
    protection = models.IntegerField(_("protection"), default=0)

    perception = models.IntegerField(_("perception"), default=2)

    actions = models.IntegerField(_("actions"), default=2)
    quickness = models.IntegerField(_("quickness"), default=1)
    walking_range = models.IntegerField(_("walking range"), default=4)
    minimum_roll = models.IntegerField(_("minimum roll"), default=5)

    stress_test_succeeded_stress = models.IntegerField(
        _("stress test succeeded stress"), default=0
    )
    stress_test_failed_stress = models.IntegerField(
        _("stress test failed stress"), default=0
    )

    resistances = models.ManyToManyField(
        WikiPageFoeResistanceOrWeakness,
        blank=True,
        related_name="wiki_page_game_values_resistance_set",
        verbose_name=_("resistances"),
    )
    weaknesses = models.ManyToManyField(
        WikiPageFoeResistanceOrWeakness,
        blank=True,
        related_name="wiki_page_game_values_weakness_set",
        verbose_name=_("weaknesses"),
    )

    class Meta:
        verbose_name = _("wiki page game values")
        verbose_name_plural = _("wiki page game values")
        get_latest_by = "id"

    def __str__(self):
        return f"{self.wiki_page.name} game values"

    def resistance_string(self):
        return ",".join([r.name for r in self.resistances.all()]) or "-"

    def weakness_string(self):
        return ",".join([r.name for r in self.weaknesses.all()]) or "-"


class WikiPageGameAction(models.Model, metaclass=TransMeta):
    WORK_TYPE_CHOICES = (
        ("lesser", _("Lesser")),
        ("higher", _("Higher")),
    )

    wiki_page = models.ForeignKey(
        "worlds.WikiPage",
        verbose_name=_("wiki page"),
        help_text=_("The wiki page the values belongs to."),
        on_delete=models.CASCADE,
    )

    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    modified_at = models.DateTimeField(_("modified at"), auto_now=True)
    name = models.CharField(_("name"), max_length=256)
    skill = models.IntegerField(_("skill"), default=6)
    effect = models.TextField(_("effect"))
    entity_work_type = models.CharField(
        _("entity work type"),
        help_text=_("Leave this empty if the Wikipage doesn't describe an entity."),
        max_length=6,
        choices=WORK_TYPE_CHOICES,
        blank=True,
        null=True,
    )

    class Meta:
        translate = ("name", "effect")
        verbose_name = _("wiki page game action")
        verbose_name_plural = _("wiki page game actions")


class WikiPageEmbedding(models.Model):
    wiki_page = models.ForeignKey(
        "worlds.WikiPage",
        verbose_name=_("wiki page"),
        help_text=_("The wiki page the embedding belongs to."),
        on_delete=models.CASCADE,
    )

    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    modified_at = models.DateTimeField(_("modified at"), auto_now=True)

    character = models.ForeignKey(
        "characters.Character", blank=True, null=True, on_delete=models.SET_NULL
    )
    spell_origin = models.ForeignKey(
        "magic.SpellOrigin", blank=True, null=True, on_delete=models.SET_NULL
    )


class LanguageGroup(models.Model, metaclass=TransMeta):
    name = models.CharField(_("name"), max_length=100)

    class Meta:
        translate = ("name",)
        verbose_name = _("language group")
        verbose_name_plural = _("language groups")

    def __str__(self):
        return self.name

    def child_item_qs(self):
        return self.language_set.all()


class LanguageQuerySet(HomebrewQuerySet):
    pass


class Language(HomebrewModel, metaclass=TransMeta):
    objects = LanguageQuerySet.as_manager()

    name = models.CharField(_("name"), max_length=100)
    country_name = models.CharField(_("country name"), max_length=100)
    amount_of_people_speaking = models.IntegerField(_("amount of people speaking"))
    group = models.ForeignKey(
        LanguageGroup,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        verbose_name=_("group"),
    )
    extensions = models.ManyToManyField(
        "rules.Extension",
        blank=True,
        related_name="languages",
        verbose_name=_("extensions"),
    )

    class Meta:
        translate = ("name", "country_name")
        ordering = ("-amount_of_people_speaking",)
        verbose_name = _("language")
        verbose_name_plural = _("languages")

    def __str__(self):
        return self.name
