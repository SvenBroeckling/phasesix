# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from rules.models import Skill, Extension, Shadow, Knowledge, Template, TemplateModifier, TemplateRequirement, \
    TemplateCategory


class TemplateModifierInline(admin.TabularInline):
    model = TemplateModifier


class TemplateRequirementInline(admin.TabularInline):
    model = TemplateRequirement
    fk_name = 'template'


class TemplateAdmin(admin.ModelAdmin):
    inlines = [TemplateModifierInline, TemplateRequirementInline]
    list_display = ('name', 'extension', 'category')
    list_filter = ('extension', 'category')


admin.site.register(Extension)
admin.site.register(Skill)
admin.site.register(Knowledge)
admin.site.register(Shadow)
admin.site.register(TemplateCategory)
admin.site.register(Template, TemplateAdmin)
