from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin, TabularInline

from body_modifications.models import (
    SocketLocation,
    BodyModificationType,
    BodyModification,
    BodyModificationSocketLocation,
)


@admin.register(SocketLocation)
class LocationAdmin(ModelAdmin):
    pass


@admin.register(BodyModificationType)
class BodyModificationTypeAdmin(ModelAdmin):
    pass


class BodyModificationSocketLocationInline(TabularInline):
    model = BodyModificationSocketLocation
    extra = 0


@admin.register(BodyModification)
class BodyModificationAdmin(ModelAdmin):
    inlines = [BodyModificationSocketLocationInline]
    search_fields = ("name_en", "name_de")
    list_display = (
        "name",
        "type",
        "rarity",
        "price",
        "bio_strain",
        "energy_consumption_ma",
        "activation",
    )
    list_filter = (
        "type",
        "rarity",
        "bio_strain",
        "energy_consumption_ma",
        "activation",
    )
    list_editable = ("rarity", "price", "bio_strain", "energy_consumption_ma")
    fieldsets = [
        (
            None,
            {
                "fields": (
                    ("name_en", "name_de"),
                    ("description_en", "description_de"),
                    ("rules_en", "rules_de"),
                    (
                        "type",
                        "rarity",
                        "price",
                    ),
                    ("bio_strain", "energy_consumption_ma", "charges"),
                    ("usable_in_combat",),
                    (
                        "activation",
                        "dice_roll_string",
                    ),
                    (
                        "attribute",
                        "skill",
                        "knowledge",
                    ),
                ),
            },
        ),
        (
            _("Image"),
            {
                "fields": (
                    "image",
                    (
                        "image_copyright",
                        "image_copyright_url",
                    ),
                ),
                "classes": ("collapse",),
            },
        ),
        (
            _("Homebrew"),
            {
                "fields": (
                    (
                        "is_homebrew",
                        "keep_as_homebrew",
                    ),
                    "created_by",
                    (
                        "homebrew_campaign",
                        "homebrew_character",
                    ),
                ),
                "classes": ("collapse",),
            },
        ),
    ]
