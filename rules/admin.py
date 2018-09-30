# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from rules.models import Skill, Extension, Shadow, Knowledge, Template, TemplateModifier, TemplateRequirement, \
    TemplateCategory, LineageTemplatePoints, Lineage


class TemplateModifierInline(admin.TabularInline):
    model = TemplateModifier


class TemplateRequirementInline(admin.TabularInline):
    model = TemplateRequirement
    fk_name = 'template'


class TemplateAdmin(admin.ModelAdmin):
    inlines = [TemplateModifierInline, TemplateRequirementInline]
    list_display = ('name', 'cost', 'extension', 'category')
    list_filter = ('extension', 'category')
    list_editable = ('category', 'cost')


class SkillAdmin(admin.ModelAdmin):
    list_display = ('name_de', 'name_en', 'kind', 'extension')
    list_editable = ('kind',)


class LineageTemplatePointsInline(admin.TabularInline):
    model = LineageTemplatePoints


class LineageAdmin(admin.ModelAdmin):
    inlines = [LineageTemplatePointsInline]

admin.site.register(Extension)
admin.site.register(Skill, SkillAdmin)
admin.site.register(Knowledge)
admin.site.register(Shadow)
admin.site.register(TemplateCategory)
admin.site.register(Template, TemplateAdmin)
admin.site.register(Lineage, LineageAdmin)
