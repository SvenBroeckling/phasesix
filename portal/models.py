from django.db import models
from django.utils.translation import gettext_lazy as _
from sorl.thumbnail import get_thumbnail

from characters.utils import static_thumbnail


class Profile(models.Model):
    user = models.OneToOneField("auth.User", on_delete=models.CASCADE)
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)

    image = models.ImageField(
        _("image"), upload_to="profile_images", max_length=200, blank=True, null=True
    )
    image_copyright = models.CharField(
        _("image copyright"), max_length=40, blank=True, null=True
    )
    image_copyright_url = models.CharField(
        _("image copyright url"), max_length=150, blank=True, null=True
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

    def __str__(self):
        return self.user.username

    class Meta:
        verbose_name = _("Profile")
        verbose_name_plural = _("Profiles")

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
