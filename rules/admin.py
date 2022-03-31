# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from rules.models import Skill, Extension, Shadow, Knowledge, Template, TemplateModifier, TemplateRequirement, \
    TemplateCategory, LineageTemplatePoints, Lineage, StatusEffect, Attribute


class ExtensionAdmin(admin.ModelAdmin):
    list_display = ('name_de', 'name_en', 'identifier', 'is_mandatory', 'fa_icon_class', 'is_epoch', 'is_active', 'ordering', 'image')
    list_filter = ('is_mandatory', 'is_epoch', 'is_active')
    list_editable = ('ordering', 'is_active')


class TemplateModifierInline(admin.TabularInline):
    model = TemplateModifier


class TemplateRequirementInline(admin.TabularInline):
    model = TemplateRequirement
    fk_name = 'template'


class TemplateCategoryAdmin(admin.ModelAdmin):
    list_display = ('name_de', 'name_en', 'bg_color_class', 'fg_color_class', 'sort_order')
    list_editable = ('bg_color_class', 'fg_color_class', 'sort_order')


class TemplateAdmin(admin.ModelAdmin):
    inlines = [TemplateModifierInline, TemplateRequirementInline]
    search_fields = ('name_de', 'name_en')
    list_display = (
        'name', 'cost', 'category', 'has_rules', 'show_rules_in_shadows', 'show_rules_in_combat', 'has_quote')
    list_editable = ('category', 'cost', 'show_rules_in_shadows', 'show_rules_in_combat')
    list_filter = ('extensions', 'category')
    save_as = True


class AttributeAdmin(admin.ModelAdmin):
    list_display = ('name_de', 'name_en', 'kind')
    list_editable = ('kind',)


class SkillAdmin(admin.ModelAdmin):
    list_display = ('name_de', 'name_en', 'kind', 'reference_attribute_1', 'reference_attribute_2')
    list_editable = ('kind',)


class KnowledgeAdmin(admin.ModelAdmin):
    list_display = ('name_de', 'name_en', 'skill')
    list_editable = 'skill',


class LineageTemplatePointsInline(admin.TabularInline):
    model = LineageTemplatePoints


class LineageAdmin(admin.ModelAdmin):
    inlines = [LineageTemplatePointsInline]


class StatusEffectAdmin(admin.ModelAdmin):
    list_display = ('name_de', 'name_en', 'fa_icon_class', 'is_active')
    list_editable = 'is_active',


admin.site.register(Extension, ExtensionAdmin)
admin.site.register(Attribute, AttributeAdmin)
admin.site.register(Skill, SkillAdmin)
admin.site.register(Knowledge, KnowledgeAdmin)
admin.site.register(Shadow)
admin.site.register(TemplateCategory, TemplateCategoryAdmin)
admin.site.register(Template, TemplateAdmin)
admin.site.register(Lineage, LineageAdmin)
admin.site.register(StatusEffect, StatusEffectAdmin)
