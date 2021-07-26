from django.contrib import admin

from magic.models import BaseSpell, SpellType, SpellVariant, SpellShape, SpellTemplate, SpellTemplateModifier


class BaseSpellAdmin(admin.ModelAdmin):
    list_display = ('name_de', 'name_en', 'cost', 'type', 'variant', 'power', 'range', 'actions')
    list_filter = ('cost', 'type', 'variant', 'power', 'range', 'actions')


class SpellTemplateModifierInline(admin.TabularInline):
    model = SpellTemplateModifier


class SpellTemplateAdmin(admin.ModelAdmin):
    inlines = [SpellTemplateModifierInline]


admin.site.register(BaseSpell, BaseSpellAdmin)
admin.site.register(SpellTemplate, SpellTemplateAdmin)
admin.site.register(SpellTemplateModifier)
admin.site.register(SpellShape)
admin.site.register(SpellType)
admin.site.register(SpellVariant)
