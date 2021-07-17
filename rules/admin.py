# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from rules.models import Skill, Extension, Shadow, Knowledge, Template, TemplateModifier, TemplateRequirement, \
    TemplateCategory, LineageTemplatePoints, Lineage, StatusEffect


class ExtensionAdmin(admin.ModelAdmin):
    list_display = ('name_de', 'name_en', 'is_mandatory', 'fa_icon_class', 'is_epoch', 'is_active', 'ordering', 'image')
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


class SkillAdmin(admin.ModelAdmin):
    list_display = ('name_de', 'name_en', 'kind', 'show_on_combat_tab', 'dominant_attribute', 'supplemental_attribute')
    list_editable = ('kind', 'show_on_combat_tab')


class KnowledgeAdmin(admin.ModelAdmin):
    list_display = ('name_de', 'name_en', 'skill')
    list_editable = 'skill',


class LineageTemplatePointsInline(admin.TabularInline):
    model = LineageTemplatePoints


class LineageAdmin(admin.ModelAdmin):
    inlines = [LineageTemplatePointsInline]


class StatusEffectAdmin(admin.ModelAdmin):
    list_display = ('name_de', 'name_en', 'fa_icon_class')


admin.site.register(Extension, ExtensionAdmin)
admin.site.register(Skill, SkillAdmin)
admin.site.register(Knowledge, KnowledgeAdmin)
admin.site.register(Shadow)
admin.site.register(TemplateCategory, TemplateCategoryAdmin)
admin.site.register(Template, TemplateAdmin)
admin.site.register(Lineage, LineageAdmin)
admin.site.register(StatusEffect, StatusEffectAdmin)
