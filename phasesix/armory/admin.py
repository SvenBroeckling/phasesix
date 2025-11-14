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
    ItemBrewingEffect,
)
from portal.admin import ShortDescriptionListFilter, ShortRulesListFilter


class WeaponKeywordInline(TabularInline):
    model = WeaponKeyword


@admin.register(Weapon)
class WeaponAdmin(ModelAdmin):
    list_display = (
        "name_de",
        "name_en",
        "price",
    )
    list_filter = (
        ShortDescriptionListFilter,
        "is_hand_to_hand_weapon",
        "is_homebrew",
        "type",
        "extensions",
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


@admin.register(ProtectionType)
class ProtectionTypeAdmin(ModelAdmin):
    list_display = (
        "name_en",
        "name_de",
        "ordering",
        "letter_de",
        "letter_en",
        "color_class",
        "icon_class",
    )
    list_editable = ("ordering", "color_class", "icon_class", "letter_de", "letter_en")


class RiotGearProtectionInline(TabularInline):
    model = RiotGearProtection


class RiotGearModifierInline(TabularInline):
    model = RiotGearModifier


@admin.register(RiotGear)
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
    list_filter = (ShortDescriptionListFilter, "is_homebrew", "extensions", "type")
    filter_horizontal = ("extensions",)
    search_fields = "name_de", "name_en"
    fieldsets = [
        (
            None,
            {
                "fields": (
                    ("name_de", "name_en"),
                    "extensions",
                    ("type", "price", "weight"),
                    ("shield_cover",),
                    ("concealment", "encumbrance"),
                    ("description_de", "description_en"),
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


@admin.register(ItemType)
class ItemTypeAdmin(ModelAdmin):
    list_display = ("name_en", "name_de", "ordering")
    list_editable = ("ordering",)


@admin.register(ItemBrewingEffect)
class ItemBrewingEffectAdmin(ModelAdmin):
    pass


@admin.register(Item)
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
    list_filter = (ShortDescriptionListFilter, "type", "extensions")
    filter_horizontal = ("extensions",)
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
                    "brewing_effect",
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


@admin.register(WeaponType)
class WeaponTypeAdmin(ModelAdmin):
    list_display = ("name_en", "name_de", "ordering")
    list_editable = ("ordering",)


@admin.register(RiotGearType)
class RiotGearTypeAdmin(ModelAdmin):
    list_display = ("name_en", "name_de", "ordering")
    list_editable = ("ordering",)


@admin.register(WeaponModificationType)
class WeaponModificationTypeAdmin(ModelAdmin):
    list_display = ("name_de", "name_en", "unique_equip")


class WeapomModificationKeywordInline(TabularInline):
    model = WeaponModificationKeyword


@admin.register(WeaponModification)
class WeaponModificationAdmin(ModelAdmin):
    list_display = ("name_de", "name_en", "type", "extension_string", "price")
    list_filter = (
        ShortDescriptionListFilter,
        ShortRulesListFilter,
        "type",
    )
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


@admin.register(AttackMode)
class AttackModeAdmin(ModelAdmin):
    list_display = ("name_de", "name_en", "dice_bonus")
    list_editable = ("dice_bonus",)


class CurrencyMapUnitInline(TabularInline):
    model = CurrencyMapUnit


@admin.register(CurrencyMap)
class CurrencyMapAdmin(ModelAdmin):
    inlines = [CurrencyMapUnitInline]


@admin.register(CurrencyMapUnit)
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


@admin.register(Keyword)
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
