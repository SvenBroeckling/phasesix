from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline

from rules.models import (
    Skill,
    Extension,
    Knowledge,
    Template,
    TemplateModifier,
    TemplateRequirement,
    TemplateCategory,
    Lineage,
    StatusEffect,
    Attribute,
)


class ExtensionAdmin(ModelAdmin):
    list_display = (
        "name_de",
        "name_en",
        "identifier",
        "is_mandatory",
        "fa_icon_class",
        "type",
        "is_active",
        "ordering",
        "image",
    )
    list_filter = ("is_mandatory", "type", "is_active")
    list_editable = ("ordering", "is_active", "type")


class TemplateModifierInline(TabularInline):
    model = TemplateModifier


class TemplateRequirementInline(TabularInline):
    model = TemplateRequirement
    fk_name = "template"


class TemplateCategoryAdmin(ModelAdmin):
    list_display = (
        "name_de",
        "name_en",
        "bg_color_class",
        "fg_color_class",
        "sort_order",
    )
    list_editable = ("bg_color_class", "fg_color_class", "sort_order")


class TemplateAdmin(ModelAdmin):
    inlines = [TemplateModifierInline, TemplateRequirementInline]
    search_fields = ("name_de", "name_en", "rules_de", "rules_en")
    list_display = (
        "name",
        "cost",
        "category",
        "has_rules",
        "is_mastery",
        "show_rules_in_combat",
        "has_quote",
    )
    list_editable = ("category", "cost", "show_rules_in_combat", "is_mastery")
    list_filter = ("extensions", "category", "extensions")
    save_as = True


class AttributeAdmin(ModelAdmin):
    list_display = ("name_de", "name_en", "kind")
    list_editable = ("kind",)


class SkillAdmin(ModelAdmin):
    list_display = (
        "name_de",
        "name_en",
        "kind",
        "reference_attribute_1",
        "reference_attribute_2",
    )
    list_editable = ("kind", "reference_attribute_1", "reference_attribute_2")


class KnowledgeAdmin(ModelAdmin):
    list_display = ("name_de", "name_en", "skill")
    list_editable = ("skill",)


class LineageAdmin(ModelAdmin):
    list_display = (
        "name_de",
        "name_en",
        "template_points",
        "template",
        "base_max_health",
    )
    list_editable = ("base_max_health",)


class StatusEffectAdmin(ModelAdmin):
    list_display = ("name_de", "name_en", "fa_icon_class", "is_active")
    list_editable = ("is_active",)


admin.site.register(Extension, ExtensionAdmin)
admin.site.register(Attribute, AttributeAdmin)
admin.site.register(Skill, SkillAdmin)
admin.site.register(Knowledge, KnowledgeAdmin)
admin.site.register(TemplateCategory, TemplateCategoryAdmin)
admin.site.register(Template, TemplateAdmin)
admin.site.register(Lineage, LineageAdmin)
admin.site.register(StatusEffect, StatusEffectAdmin)
