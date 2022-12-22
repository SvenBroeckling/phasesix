from django.contrib import admin
from reversion.admin import VersionAdmin

from magic.models import BaseSpell, SpellType, SpellVariant, SpellShape, SpellTemplate, SpellTemplateModifier, \
    SpellTemplateCategory, SpellOrigin


class BaseSpellAdmin(VersionAdmin):
    list_display = (
        'name_de', 'name_en', 'spell_point_cost', 'origin', 'type', 'variant', 'power', 'range', 'actions',
        'is_tirakan_spell')
    list_editable = ('spell_point_cost', 'origin', 'power', 'range', 'actions', 'is_tirakan_spell',)
    search_fields = ('name_de', 'name_en')
    list_filter = (
        'spell_point_cost', 'arcana_cost', 'type', 'variant', 'power', 'range', 'actions', 'is_tirakan_spell')
    fields = (
        ('name_de', 'name_en', 'is_tirakan_spell'),
        ('created_by', 'is_homebrew', 'homebrew_campaign', 'keep_as_homebrew'),
        ('spell_point_cost', 'arcana_cost', 'power', 'range', 'actions'),
        ('origin', 'type', 'variant', 'shape'),
        'is_ritual',
        ('rules_de', 'rules_en'),
        ('quote', 'quote_author'),
    )


class SpellTemplateModifierInline(admin.TabularInline):
    model = SpellTemplateModifier


class SpellTemplateAdmin(VersionAdmin):
    list_display = ('name_de', 'name_en', 'category', 'spell_point_cost')
    list_editable = 'category', 'spell_point_cost'
    list_filter = 'spell_point_cost', 'category'
    inlines = [SpellTemplateModifierInline]
    fields = (
        ('name_de', 'name_en'),
        ('category', 'spell_point_cost'),
        ('rules_de', 'rules_en'),
        ('quote', 'quote_author'),
    )


class SpellTypeAdmin(VersionAdmin):
    list_display = ('name_de', 'name_en', 'image', 'reference_attribute')
    list_editable = 'reference_attribute',


admin.site.register(SpellOrigin)
admin.site.register(BaseSpell, BaseSpellAdmin)
admin.site.register(SpellTemplateCategory, VersionAdmin)
admin.site.register(SpellTemplate, SpellTemplateAdmin)
admin.site.register(SpellTemplateModifier, VersionAdmin)
admin.site.register(SpellShape, VersionAdmin)
admin.site.register(SpellType, SpellTypeAdmin)
admin.site.register(SpellVariant, VersionAdmin)
