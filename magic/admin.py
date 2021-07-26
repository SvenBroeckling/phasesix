from django.contrib import admin

from magic.models import BaseSpell, SpellType, SpellVariant, SpellShape, SpellTemplate, SpellTemplateModifier


class BaseSpellAdmin(admin.ModelAdmin):
    list_display = ('name_de', 'name_en', 'cost', 'type', 'variant', 'power', 'range', 'actions')
    list_filter = ('cost', 'type', 'variant', 'power', 'range', 'actions')
    fields = (
        ('name_de', 'name_en'),
        ('cost', 'power', 'range', 'actions'),
        ('variant', 'type', 'shape'),
        'is_ritual',
        ('rules_de', 'rules_en'),
        ('quote', 'quote_author'),
    )


class SpellTemplateModifierInline(admin.TabularInline):
    model = SpellTemplateModifier


class SpellTemplateAdmin(admin.ModelAdmin):
    list_display = ('name_de', 'name_en', 'cost')
    list_filter = 'cost',
    inlines = [SpellTemplateModifierInline]
    fields = (
        ('name_de', 'name_en'),
        'cost',
        ('rules_de', 'rules_en'),
        ('quote', 'quote_author'),
    )


class SpellTypeAdmin(admin.ModelAdmin):
    list_display = ('name_de', 'name_en', 'image')

admin.site.register(BaseSpell, BaseSpellAdmin)
admin.site.register(SpellTemplate, SpellTemplateAdmin)
admin.site.register(SpellTemplateModifier)
admin.site.register(SpellShape)
admin.site.register(SpellType, SpellTypeAdmin)
admin.site.register(SpellVariant)
