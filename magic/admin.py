from django.contrib import admin

from magic.models import SpellCost, SpellRange, SpellAreaOfEffect, SpellComponents, SpellCastingTime, SpellType, \
    SpellPower, SpellFlavour, SpellAreaOfEffectRange, SpellRule


class SpellComponentAdmin(admin.ModelAdmin):
    list_display = ('name_de', 'name_en', 'cost')
    list_editable = ('cost',)


class SpellRuleAdmin(admin.ModelAdmin):
    list_display = ('flavour', 'power', 'rule_text_de', 'rule_text_en')
    list_filter = ('flavour', 'power')


class SpellFlavourInline(admin.TabularInline):
    model = SpellFlavour


class SpellTypeAdmin(SpellComponentAdmin):
    inlines = [SpellFlavourInline]

admin.site.register(SpellCost, SpellComponentAdmin)
admin.site.register(SpellRange, SpellComponentAdmin)
admin.site.register(SpellAreaOfEffect, SpellComponentAdmin)
admin.site.register(SpellAreaOfEffectRange, SpellComponentAdmin)
admin.site.register(SpellComponents, SpellComponentAdmin)
admin.site.register(SpellCastingTime, SpellComponentAdmin)
admin.site.register(SpellType, SpellTypeAdmin)
admin.site.register(SpellPower, SpellComponentAdmin)
admin.site.register(SpellFlavour, SpellComponentAdmin)
admin.site.register(SpellRule, SpellRuleAdmin)
