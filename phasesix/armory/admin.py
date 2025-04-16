from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin, TabularInline

from armory.models import (
    WeaponType,
    Weapon,
    WeaponModificationType,
    WeaponModification,
    RiotGear,
    ItemType,
    Item,
    AttackMode,
    CurrencyMap,
    CurrencyMapUnit,
    RiotGearType,
    Keyword,
    WeaponKeyword,
    WeaponModificationKeyword,
    RiotGearProtection,
    ProtectionType,
    RiotGearModifier,
)


class WeaponKeywordInline(TabularInline):
    model = WeaponKeyword


class WeaponAdmin(ModelAdmin):
    list_display = (
        "name_de",
        "name_en",
        "price",
    )
    list_filter = (
        "type",
        "extensions",
        "is_hand_to_hand_weapon",
    )
    search_fields = "name_en", "name_de"
    inlines = [WeaponKeywordInline]
    filter_horizontal = ("extensions", "attack_modes")
    fieldsets = [
        (
            None,
            {
                "fields": (
                    (
                        "name_de",
                        "name_en",
                        "is_hand_to_hand_weapon",
                        "is_throwing_weapon",
                    ),
                    ("extensions",),
                    ("attack_modes",),
                    ("type", "weight", "price"),
                    (
                        "description_de",
                        "description_en",
                    ),
                    ("image", "image_copyright", "image_copyright_url"),
                )
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


class ProtectionTypeAdmin(ModelAdmin):
    list_display = ("name_en", "name_de", "ordering", "color_class", "icon_class")
    list_editable = ("ordering", "color_class", "icon_class")


class RiotGearProtectionInline(TabularInline):
    model = RiotGearProtection


class RiotGearModifierInline(TabularInline):
    model = RiotGearModifier


class RiotGearAdmin(ModelAdmin):
    list_display = (
        "name_de",
        "name_en",
        "type",
        "price",
        "encumbrance",
        "concealment",
        "shield_cover",
        "weight",
    )
    list_editable = (
        "weight",
        "price",
        "encumbrance",
        "shield_cover",
        "concealment",
    )
    inlines = [RiotGearProtectionInline, RiotGearModifierInline]
    list_filter = ("extensions", "type")
    search_fields = "name_de", "name_en"
    fieldsets = [
        (
            None,
            {
                "fields": (
                    ("name_en", "name_de"),
                    "extensions",
                    ("type", "price", "weight"),
                    ("shield_cover",),
                    ("concealment", "encumbrance"),
                    ("description_en", "description_de"),
                )
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


class ItemTypeAdmin(ModelAdmin):
    list_display = ("name_en", "name_de", "ordering")
    list_editable = ("ordering",)


class ItemAdmin(ModelAdmin):
    list_display = (
        "name_de",
        "name_en",
        "type",
        "weight",
        "rarity",
        "price",
        "is_container",
        "skill",
        "concealment",
        "usable_in_combat",
    )
    list_editable = (
        "concealment",
        "type",
        "rarity",
        "is_container",
        "usable_in_combat",
        "skill",
    )
    list_filter = ("type", "extensions")
    search_fields = ("name_de", "name_en", "description_de", "description_en")
    fieldsets = [
        (
            None,
            {
                "fields": (
                    ("name_en", "name_de"),
                    ("type", "rarity", "price"),
                    ("weight", "concealment", "charges"),
                    ("usable_in_combat", "is_container"),
                    "extensions",
                    ("description_en", "description_de"),
                    ("skill", "attribute", "knowledge"),
                    "dice_roll_string",
                    ("image", "image_copyright", "image_copyright_url"),
                ),
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


class WeaponTypeAdmin(ModelAdmin):
    list_display = ("name_en", "name_de", "ordering")
    list_editable = ("ordering",)


class RiotGearTypeAdmin(ModelAdmin):
    list_display = ("name_en", "name_de", "ordering")
    list_editable = ("ordering",)


class WeaponModificationTypeAdmin(ModelAdmin):
    list_display = ("name_de", "name_en", "unique_equip")


class WeapomModificationKeywordInline(TabularInline):
    model = WeaponModificationKeyword


class WeaponModificationAdmin(ModelAdmin):
    list_display = ("name_de", "name_en", "type", "extension_string", "price")
    list_filter = ("type",)
    search_fields = "name_de", "name_en"
    filter_horizontal = ("extensions", "available_for_weapon_types")
    inlines = [WeapomModificationKeywordInline]
    fieldsets = [
        (
            None,
            {
                "fields": (
                    ("name_de", "name_en"),
                    ("type", "price"),
                    ("extensions",),
                    ("available_for_weapon_types"),
                    ("description_de", "description_en"),
                    ("rules_de", "rules_en"),
                )
            },
        ),
    ]


class AttackModeAdmin(ModelAdmin):
    list_display = ("name_de", "name_en", "dice_bonus")
    list_editable = ("dice_bonus",)


class CurrencyMapUnitInline(TabularInline):
    model = CurrencyMapUnit


class CurrencyMapAdmin(ModelAdmin):
    inlines = [CurrencyMapUnitInline]


class CurrencyMapUnitAdmin(ModelAdmin):
    list_display = (
        "name_de",
        "name_en",
        "currency_map",
        "ordering",
        "is_common",
        "value",
    )
    list_editable = ("name_en", "ordering", "is_common", "value")
    list_filter = ("currency_map", "is_common")


class KeywordAdmin(ModelAdmin):
    list_display = (
        "name_de",
        "name_en",
        "is_rare",
        "ordering",
        "is_evergreen",
        "show_in_summary",
    )
    list_editable = ("ordering", "is_rare", "is_evergreen", "show_in_summary")


admin.site.register(AttackMode, AttackModeAdmin)
admin.site.register(WeaponType, WeaponTypeAdmin)
admin.site.register(Keyword, KeywordAdmin)
admin.site.register(Weapon, WeaponAdmin)
admin.site.register(WeaponModificationType, WeaponModificationTypeAdmin)
admin.site.register(WeaponModification, WeaponModificationAdmin)
admin.site.register(ProtectionType, ProtectionTypeAdmin)
admin.site.register(RiotGearType, RiotGearTypeAdmin)
admin.site.register(RiotGear, RiotGearAdmin)
admin.site.register(ItemType, ItemTypeAdmin)
admin.site.register(Item, ItemAdmin)
admin.site.register(CurrencyMap, CurrencyMapAdmin)
admin.site.register(CurrencyMapUnit, CurrencyMapUnitAdmin)
