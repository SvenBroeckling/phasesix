import uuid

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class Pad(models.Model):
    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False, verbose_name=_("ID")
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created at"))
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="party_pads",
        verbose_name=_("Created by"),
    )
    campaign = models.ForeignKey(
        "campaigns.Campaign",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="party_pads",
        verbose_name=_("Campaign"),
    )

    def __str__(self) -> str:
        return f"PartyPad {self.id}"

    def as_dict(self) -> dict:
        return {
            "id": str(self.id),
            "objects": [
                obj.as_dict() for obj in self.pad_objects.order_by("created_at")
            ],
        }


class PadObject(models.Model):
    class ObjectType(models.TextChoices):
        IMAGE = "image", "Image"
        VIDEO = "video", "Video"
        AUDIO = "audio", "Audio"
        TOKEN = "token", "Token"

    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False, verbose_name=_("ID")
    )
    object_type = models.CharField(
        max_length=16, choices=ObjectType.choices, verbose_name=_("Object type")
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created at"))
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="pad_objects",
        verbose_name=_("Created by"),
    )
    pad = models.ForeignKey(
        Pad,
        on_delete=models.CASCADE,
        related_name="pad_objects",
        verbose_name=_("Pad"),
    )
    x = models.IntegerField(verbose_name=_("X position"))
    y = models.IntegerField(verbose_name=_("Y position"))
    width = models.IntegerField(verbose_name=_("Width"))
    height = models.IntegerField(verbose_name=_("Height"))
    rotation = models.IntegerField(default=0, verbose_name=_("Rotation"))
    file = models.FileField(
        upload_to="partypad/",
        null=True,
        blank=True,
        verbose_name=_("File"),
    )
    playing = models.BooleanField(default=False, verbose_name=_("Playing"))
    loop = models.BooleanField(default=False, verbose_name=_("Loop"))

    def __str__(self) -> str:
        return f"{self.object_type}:{self.id}"

    def as_dict(self) -> dict:
        from django.urls import reverse

        return {
            "id": str(self.id),
            "object_type": self.object_type,
            "x": self.x,
            "y": self.y,
            "width": self.width,
            "height": self.height,
            "rotation": self.rotation,
            "file": self.file.name if self.file else None,
            "file_url": self.file.url if self.file else None,
            "playing": self.playing,
            "loop": self.loop,
            "modify_url": reverse(
                "partypad:modify_object_specific",
                kwargs={"pad_id": self.pad_id, "object_id": self.id},
            ),
        }
