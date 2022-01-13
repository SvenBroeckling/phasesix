from django.contrib import admin

from armory.models import WeaponModificationAttributeChange, WeaponType, Weapon, WeaponModificationType, \
    WeaponModification, RiotGear, ItemType, Item, AttackMode, WeaponAttackMode, CurrencyMap, CurrencyMapUnit


class WeaponAttackModeInline(admin.TabularInline):
    model = WeaponAttackMode


class WeaponAdmin(admin.ModelAdmin):
    list_display = (
        'name_en', 'capacity', 'wounds', 'piercing', 'reload_actions', 'weight', 'price', 'range_meter')
    list_editable = (
        'capacity', 'wounds', 'piercing', 'weight', 'reload_actions', 'price', 'range_meter')
    list_filter = ('type', 'extensions', 'is_hand_to_hand_weapon')
    inlines = [WeaponAttackModeInline]
    fieldsets = [
        (None, {
            'fields': (
                ('name_en', 'name_de', 'extensions', 'is_hand_to_hand_weapon'),
                ('type', 'capacity', 'wounds', 'piercing', 'weight'),
                ('range_meter', 'concealment', 'price', 'reload_actions', 'bonus_dice'),
                ('description_en', 'description_de',),
                ('image', 'image_copyright', 'image_copyright_url')
            )
        }),
    ]


class RiotGearAdmin(admin.ModelAdmin):
    list_display = ('name_de', 'name_en', 'weight', 'price', 'protection_ballistic',
                    'evasion', 'concealment')
    list_editable = ('weight', 'price', 'protection_ballistic', 'evasion', 'concealment')
    list_filter = ('extensions',)
    fieldsets = [
        (None, {
            'fields': (
                ('name_en', 'name_de', 'extensions'),
                ('price', 'weight'),
                ('protection_ballistic',),
                ('concealment', 'evasion'),
                ('description_en', 'description_de'),
            )
        }),
    ]


class ItemAdmin(admin.ModelAdmin):
    list_display = ('name_de', 'name_en', 'type', 'weight', 'price', 'concealment', 'usable_in_combat')
    list_editable = ('concealment', 'type', 'usable_in_combat')
    list_filter = ('type', 'extensions')


class WeaponTypeAdmin(admin.ModelAdmin):
    list_display = ('name_en', 'name_de')


class WeaponModificationAttributeChangeInline(admin.TabularInline):
    model = WeaponModificationAttributeChange


class WeaponModificationAdmin(admin.ModelAdmin):
    list_display = ('name_de', 'name_en', 'type', 'price')
    inlines = [WeaponModificationAttributeChangeInline]


class AttackModeAdmin(admin.ModelAdmin):
    list_display = ('name_de', 'name_en', 'dice_bonus')
    list_editable = ('dice_bonus',)


class CurrencyMapUnitInline(admin.TabularInline):
    model = CurrencyMapUnit


class CurrencyMapAdmin(admin.ModelAdmin):
    inlines = [CurrencyMapUnitInline]


admin.site.register(AttackMode, AttackModeAdmin)
admin.site.register(WeaponType, WeaponTypeAdmin)
admin.site.register(Weapon, WeaponAdmin)
admin.site.register(WeaponModificationType)
admin.site.register(WeaponModification, WeaponModificationAdmin)
admin.site.register(RiotGear, RiotGearAdmin)
admin.site.register(ItemType)
admin.site.register(Item, ItemAdmin)
admin.site.register(CurrencyMap, CurrencyMapAdmin)
admin.site.register(CurrencyMapUnit)
