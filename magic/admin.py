from django.contrib import admin

from magic.models import BaseSpell, SpellType, SpellVariant, SpellShape, SpellTemplate, SpellTemplateModifier


class BaseSpellAdmin(admin.ModelAdmin):
    list_display = (
        'name_de', 'name_en', 'spell_point_cost', 'arcana_cost', 'type', 'variant', 'power', 'range', 'actions',
        'is_tirakan_spell')
    list_editable = ('is_tirakan_spell',)
    list_filter = (
        'spell_point_cost', 'arcana_cost', 'type', 'variant', 'power', 'range', 'actions', 'is_tirakan_spell')
    fields = (
        ('name_de', 'name_en', 'is_tirakan_spell'),
        ('spell_point_cost', 'arcana_cost', 'power', 'range', 'actions'),
        ('variant', 'type', 'shape'),
        'is_ritual',
        ('rules_de', 'rules_en'),
        ('quote', 'quote_author'),
    )


class SpellTemplateModifierInline(admin.TabularInline):
    model = SpellTemplateModifier


class SpellTemplateAdmin(admin.ModelAdmin):
    list_display = ('name_de', 'name_en', 'spell_point_cost')
    list_filter = 'spell_point_cost',
    inlines = [SpellTemplateModifierInline]
    fields = (
        ('name_de', 'name_en'),
        'spell_point_cost',
        ('rules_de', 'rules_en'),
        ('quote', 'quote_author'),
    )


class SpellTypeAdmin(admin.ModelAdmin):
    list_display = ('name_de', 'name_en', 'image', 'dominant_attribute', 'supplemental_attribute')
    list_editable = ('dominant_attribute', 'supplemental_attribute')


admin.site.register(BaseSpell, BaseSpellAdmin)
admin.site.register(SpellTemplate, SpellTemplateAdmin)
admin.site.register(SpellTemplateModifier)
admin.site.register(SpellShape)
admin.site.register(SpellType, SpellTypeAdmin)
admin.site.register(SpellVariant)
