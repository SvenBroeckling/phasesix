from django.contrib import admin

from magic.models import SpellCost, SpellRange, SpellAreaOfEffect, SpellComponents, SpellCastingTime, SpellType, \
    SpellPower, SpellFlavour, SpellAreaOfEffectRange

class SpellComponentAdmin(admin.ModelAdmin):
    list_display = ('name_de', 'name_en', 'cost')
    list_editable = ('cost',)


admin.site.register(SpellCost, SpellComponentAdmin)
admin.site.register(SpellRange, SpellComponentAdmin)
admin.site.register(SpellAreaOfEffect, SpellComponentAdmin)
admin.site.register(SpellAreaOfEffectRange, SpellComponentAdmin)
admin.site.register(SpellComponents, SpellComponentAdmin)
admin.site.register(SpellCastingTime, SpellComponentAdmin)
admin.site.register(SpellType, SpellComponentAdmin)
admin.site.register(SpellPower, SpellComponentAdmin)
admin.site.register(SpellFlavour, SpellComponentAdmin)

