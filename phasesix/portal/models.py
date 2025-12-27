from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from sorl.thumbnail import get_thumbnail

from characters.utils import static_thumbnail
from phasesix.models import ModelWithImage, image_upload_path
from worlds.unique_slugify import unique_slugify


class Profile(ModelWithImage):
    slug = models.SlugField(_("slug"), max_length=220)
    user = models.OneToOneField("auth.User", on_delete=models.CASCADE)
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)

    api_key = models.CharField(_("api key"), max_length=120, blank=True, null=True)

    image_upload_to = "profile_images"
    image = models.ImageField(
        _("image"),
        upload_to=image_upload_path,
        max_length=200,
        blank=True,
        null=True,
    )

    last_wiki_image_copyright = models.CharField(
        _("last wiki image copyright"), max_length=40, blank=True, null=True
    )
    last_wiki_image_copyright_url = models.CharField(
        _("last wiki image copyright url"), max_length=150, blank=True, null=True
    )

    backdrop_image = models.ImageField(
        _("backdrop image"),
        upload_to="profile_backdrop_images",
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

    bio = models.TextField(_("bio"), blank=True, null=True)

    settings_protection_display = models.CharField(
        _("protection display"),
        max_length=1,
        default="I",
        choices=(
            ("I", _("Letters")),
            ("G", _("Shield Icons")),
        ),
    )

    settings_reduce_images = models.BooleanField(
        _("reduce images"),
        help_text=_("Reduce the amount of images displayed on the site."),
        default=False,
    )

    settings_language_preference = models.CharField(
        _("language preference"),
        max_length=2,
        default="EN",
        choices=(
            ("en", _("English")),
            ("de", _("German")),
        ),
    )

    may_use_ai = models.BooleanField(
        _("may use AI"),
        default=False,
    )

    def __str__(self):
        return self.user.username

    def save(self, **kwargs):
        if not self.slug:
            unique_slugify(self, str(self.user.username))
        super().save(**kwargs)

    class Meta:
        verbose_name = _("Profile")
        verbose_name_plural = _("Profiles")

    def get_absolute_url(self):
        return reverse("portal:profile", kwargs={"slug": self.slug})

    def get_image_url(self, geometry="180", crop="center"):
        if self.image:
            return get_thumbnail(self.image, geometry, crop=crop, quality=99).url

        return static_thumbnail(
            f"img/silhouette.png",
            geometry_string=geometry,
            crop=crop,
        )

    def get_backdrop_image_url(self, geometry="1800", crop="center"):
        if self.backdrop_image:
            return get_thumbnail(
                self.backdrop_image, geometry, crop=crop, quality=99
            ).url
        return static_thumbnail(
            f"img/header-background.png",
            geometry_string=geometry,
            crop=crop,
        )
