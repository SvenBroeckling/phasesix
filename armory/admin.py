from django.contrib import admin

from armory.models import (
    WeaponModificationAttributeChange,
    WeaponType,
    Weapon,
    WeaponModificationType,
    WeaponModification,
    RiotGear,
    ItemType,
    Item,
    AttackMode,
    WeaponAttackMode,
    CurrencyMap,
    CurrencyMapUnit,
    RiotGearType,
)


class WeaponAttackModeInline(admin.TabularInline):
    model = WeaponAttackMode


class WeaponAdmin(admin.ModelAdmin):
    list_display = (
        "name_en",
        "recoil_compensation",
        "actions_to_ready",
        "damage_potential",
        "piercing",
        "encumbrance",
        "price",
        "range_meter",
    )
    list_editable = (
        "recoil_compensation",
        "actions_to_ready",
        "damage_potential",
        "piercing",
        "encumbrance",
        "price",
        "range_meter",
    )
    list_filter = (
        "type",
        "extensions",
        "is_hand_to_hand_weapon",
        "damage_potential",
        "piercing",
        "crit_minimum_roll",
    )
    search_fields = "name_en", "name_de"
    inlines = [WeaponAttackModeInline]
    fieldsets = [
        (
            None,
            {
                "fields": (
                    (
                        "name_de",
                        "name_en",
                        "extensions",
                        "is_hand_to_hand_weapon",
                        "is_throwing_weapon",
                    ),
                    ("type", "capacity", "damage_potential", "piercing"),
                    ("weight", "actions_to_ready"),
                    ("recoil_compensation", "crit_minimum_roll", "reload_actions"),
                    ("range_meter", "concealment", "price"),
                    (
                        "description_de",
                        "description_en",
                    ),
                    ("created_by", "is_homebrew", "homebrew_campaign"),
                    ("image", "image_copyright", "image_copyright_url"),
                )
            },
        ),
    ]


class RiotGearAdmin(admin.ModelAdmin):
    list_display = (
        "name_de",
        "name_en",
        "type",
        "price",
        "protection_ballistic",
        "encumbrance",
        "concealment",
        "weight",
    )
    list_editable = (
        "weight",
        "price",
        "protection_ballistic",
        "encumbrance",
        "concealment",
    )
    list_filter = ("extensions", "type")
    search_fields = "name_de", "name_en"
    fieldsets = [
        (
            None,
            {
                "fields": (
                    ("name_en", "name_de", "extensions"),
                    ("type", "price", "weight"),
                    ("created_by", "is_homebrew", "homebrew_campaign"),
                    ("protection_ballistic",),
                    ("concealment", "encumbrance"),
                    ("description_en", "description_de"),
                )
            },
        ),
    ]


class ItemTypeAdmin(admin.ModelAdmin):
    list_display = ("name_en", "name_de", "ordering")
    list_editable = ("ordering",)


class ItemAdmin(admin.ModelAdmin):
    list_display = (
        "name_de",
        "name_en",
        "type",
        "weight",
        "price",
        "is_container",
        "skill",
        "concealment",
        "usable_in_combat",
    )
    list_editable = ("concealment", "type", "is_container", "usable_in_combat", "skill")
    list_filter = ("type", "extensions")
    search_fields = ("name_de", "name_en")


class WeaponTypeAdmin(admin.ModelAdmin):
    list_display = ("name_en", "name_de", "ordering")
    list_editable = ("ordering",)


class RiotGearTypeAdmin(admin.ModelAdmin):
    list_display = ("name_en", "name_de", "ordering")
    list_editable = ("ordering",)


class WeaponModificationTypeAdmin(admin.ModelAdmin):
    list_display = ("name_de", "name_en", "unique_equip")


class WeaponModificationAttributeChangeInline(admin.TabularInline):
    model = WeaponModificationAttributeChange


class WeaponModificationAdmin(admin.ModelAdmin):
    list_display = ("name_de", "name_en", "type", "extension_string", "price")
    list_filter = ("type",)
    search_fields = "name_de", "name_en"
    filter_horizontal = ("extensions", "available_for_weapon_types")
    inlines = [WeaponModificationAttributeChangeInline]


class AttackModeAdmin(admin.ModelAdmin):
    list_display = ("name_de", "name_en", "dice_bonus")
    list_editable = ("dice_bonus",)


class CurrencyMapUnitInline(admin.TabularInline):
    model = CurrencyMapUnit


class CurrencyMapAdmin(admin.ModelAdmin):
    inlines = [CurrencyMapUnitInline]


admin.site.register(AttackMode, AttackModeAdmin)
admin.site.register(WeaponType, WeaponTypeAdmin)
admin.site.register(Weapon, WeaponAdmin)
admin.site.register(WeaponModificationType, WeaponModificationTypeAdmin)
admin.site.register(WeaponModification, WeaponModificationAdmin)
admin.site.register(RiotGearType, RiotGearTypeAdmin)
admin.site.register(RiotGear, RiotGearAdmin)
admin.site.register(ItemType, ItemTypeAdmin)
admin.site.register(Item, ItemAdmin)
admin.site.register(CurrencyMap, CurrencyMapAdmin)
admin.site.register(CurrencyMapUnit)
