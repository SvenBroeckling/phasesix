from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin, TabularInline

from body_modifications.models import (
    SocketLocation,
    BodyModificationType,
    BodyModification,
    BodyModificationSocketLocation,
    BodyModificationModifier,
)
from portal.admin import ShortDescriptionListFilter, ShortRulesListFilter


@admin.register(SocketLocation)
class LocationAdmin(ModelAdmin):
    pass


@admin.register(BodyModificationType)
class BodyModificationTypeAdmin(ModelAdmin):
    pass


class BodyModificationSocketLocationInline(TabularInline):
    model = BodyModificationSocketLocation
    extra = 0


class BodyModificationModifierInline(TabularInline):
    model = BodyModificationModifier
    extra = 0


@admin.register(BodyModification)
class BodyModificationAdmin(ModelAdmin):
    inlines = [BodyModificationSocketLocationInline, BodyModificationModifierInline]
    search_fields = ("name_en", "name_de")
    list_display = (
        "name_de",
        "name_en",
        "price",
        "bio_strain",
        "energy_consumption_ma",
        "activation",
        "has_stat_changes",
    )
    list_editable = ("price", "bio_strain", "energy_consumption_ma", "activation")
    list_filter = (
        ShortDescriptionListFilter,
        ShortRulesListFilter,
        "type",
        "rarity",
        "bio_strain",
        "energy_consumption_ma",
        "activation",
    )
    filter_horizontal = ("extensions",)
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
                    ("extensions",),
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

    @admin.display(boolean=True)
    def has_stat_changes(self, obj):
        return obj.bodymodificationmodifier_set.exists()
