from django.contrib import admin

from armory.models import WeaponModificationAttributeChange, WeaponType, Weapon, WeaponModificationType, \
    WeaponModification, RiotGear, ItemType, Item, WeaponAttackMode


class WeaponAdmin(admin.ModelAdmin):
    list_display = (
        'name_en', 'capacity', 'attacks_per_action', 'wounds',
        'recoil_control', 'penetration', 'weight', 'price', 'range_meter')
    list_editable = (
        'attacks_per_action', 'capacity', 'wounds', 'recoil_control',
        'penetration', 'weight', 'price', 'range_meter')
    list_filter = ('type', 'extensions', 'is_hand_to_hand_weapon')
    fieldsets = [
        (None, {
            'fields': (
                ('name_en', 'name_de', 'extensions', 'is_hand_to_hand_weapon'),
                ('type', 'attacks_per_action', 'capacity', 'wounds', 'penetration', 'weight'),
                ('range_meter', 'recoil_control', 'concealment', 'accuracy', 'price'),
                ('description_en', 'description_de', 'attack_modes'),
                ('image',)
            )
        }),
    ]


class RiotGearAdmin(admin.ModelAdmin):
    list_display = ('name_de', 'name_en', 'weight', 'price', 'protection_ballistic',
                    'protection_explosive', 'concealment')
    list_editable = ('weight', 'price', 'protection_ballistic', 'protection_explosive', 'concealment')
    list_filter = ('extensions',)
    fieldsets = [
        (None, {
            'fields': (
                ('name_en', 'name_de', 'extensions'),
                ('price', 'weight'),
                ('protection_ballistic', 'protection_explosive', 'concealment'),
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


class WeaponModificationAttributeChangeInline(admin.StackedInline):
    model = WeaponModificationAttributeChange


class WeaponModificationAdmin(admin.ModelAdmin):
    list_display = ('name_de', 'name_en', 'type', 'price')
    inlines = [WeaponModificationAttributeChangeInline]


admin.site.register(WeaponAttackMode)
admin.site.register(WeaponType, WeaponTypeAdmin)
admin.site.register(Weapon, WeaponAdmin)
admin.site.register(WeaponModificationType)
admin.site.register(WeaponModification, WeaponModificationAdmin)
admin.site.register(RiotGear, RiotGearAdmin)
admin.site.register(ItemType)
admin.site.register(Item, ItemAdmin)
