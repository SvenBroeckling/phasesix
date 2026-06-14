import posixpath

from django.db import models
from django.utils.translation import gettext_lazy as _


class ImageFocalPointMixin(models.Model):
    image_focal_x = models.PositiveSmallIntegerField(
        _("image focal point x"), default=50
    )
    image_focal_y = models.PositiveSmallIntegerField(
        _("image focal point y"), default=50
    )

    class Meta:
        abstract = True

    def get_image_focal_point(self, field_name="image"):
        x = getattr(self, f"{field_name}_focal_x", 50)
        y = getattr(self, f"{field_name}_focal_y", 50)
        return f"{x}% {y}%"

    def get_image_crop(self, crop="center", field_name="image"):
        if crop != "center":
            return crop
        return self.get_image_focal_point(field_name)


class PhaseSixModel(models.Model):
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    modified_at = models.DateTimeField(_("modified at"), auto_now=True)

    class Meta:
        abstract = True


def image_upload_path(instance, filename):
    upload_to = getattr(instance.__class__, "image_upload_to", None)
    if not upload_to:
        raise ValueError(f"{instance.__class__.__name__}.image_upload_to must be set")
    return posixpath.join(upload_to, filename)


class ModelWithImage(ImageFocalPointMixin):
    image_upload_to = None

    image = models.ImageField(
        _("image"),
        upload_to=image_upload_path,
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

    class Meta:
        abstract = True
