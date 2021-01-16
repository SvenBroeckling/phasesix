# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from rules.models import Skill, Extension, Shadow, Knowledge, Template, TemplateModifier, TemplateRequirement, \
    TemplateCategory, LineageTemplatePoints, Lineage, StatusEffect


class ExtensionAdmin(admin.ModelAdmin):
    list_display = ('name_de', 'name_en', 'is_mandatory', 'fa_icon_class', 'is_epoch', 'ordering', 'image')
    list_filter = ('is_mandatory', 'is_epoch')
    list_editable = ('ordering',)


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
    list_display = ('name', 'cost', 'category')
    list_filter = ('extensions', 'category')
    list_editable = ('category', 'cost')
    save_as = True


class SkillAdmin(admin.ModelAdmin):
    list_display = ('name_de', 'name_en', 'kind', 'show_on_combat_tab', 'default_persona_attribute')
    list_editable = ('kind', 'show_on_combat_tab', 'default_persona_attribute')


class LineageTemplatePointsInline(admin.TabularInline):
    model = LineageTemplatePoints


class LineageAdmin(admin.ModelAdmin):
    inlines = [LineageTemplatePointsInline]


class StatusEffectAdmin(admin.ModelAdmin):
    list_display = ('name_de', 'name_en', 'fa_icon_class')


admin.site.register(Extension, ExtensionAdmin)
admin.site.register(Skill, SkillAdmin)
admin.site.register(Knowledge)
admin.site.register(Shadow)
admin.site.register(TemplateCategory, TemplateCategoryAdmin)
admin.site.register(Template, TemplateAdmin)
admin.site.register(Lineage, LineageAdmin)
admin.site.register(StatusEffect, StatusEffectAdmin)
