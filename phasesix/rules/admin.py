from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin, TabularInline, StackedInline

from portal.admin import ShortShortDescriptionListFilter
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
    Foe,
    FoeType,
    FoeAction,
)


@admin.register(Extension)
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


@admin.register(TemplateCategory)
class TemplateCategoryAdmin(ModelAdmin):
    list_display = (
        "name_de",
        "name_en",
        "bg_color_class",
        "fg_color_class",
        "sort_order",
    )
    list_editable = ("bg_color_class", "fg_color_class", "sort_order")


@admin.register(Template)
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


@admin.register(Attribute)
class AttributeAdmin(ModelAdmin):
    list_display = ("name_de", "name_en", "kind")
    list_editable = ("kind",)


@admin.register(Skill)
class SkillAdmin(ModelAdmin):
    list_display = (
        "name_de",
        "name_en",
        "kind",
        "reference_attribute_1",
        "reference_attribute_2",
    )
    list_editable = ("kind", "reference_attribute_1", "reference_attribute_2")


@admin.register(Knowledge)
class KnowledgeAdmin(ModelAdmin):
    list_display = ("name_de", "name_en", "skill")
    list_editable = ("skill",)


@admin.register(Lineage)
class LineageAdmin(ModelAdmin):
    list_display = (
        "name_de",
        "name_en",
        "template_points",
        "template",
        "base_max_stress",
    )
    list_editable = ("base_max_stress",)


@admin.register(StatusEffect)
class StatusEffectAdmin(ModelAdmin):
    list_display = ("name_de", "name_en", "fa_icon_class", "is_active")
    list_editable = ("is_active",)


@admin.register(FoeType)
class FoeTypeAdmin(ModelAdmin):
    list_display = ("name_de", "name_en")
    search_fields = ("name_de", "name_en")


class FoeActionInline(StackedInline):
    model = FoeAction
    extra = 0
    fields = ("name_de", "name_en", "skill", "effect_de", "effect_en")
    classes = ("collapse",)


@admin.register(Foe)
class FoeAdmin(ModelAdmin):
    inlines = [FoeActionInline]
    list_display = (
        "name_de",
        "name_en",
        "type",
        "health",
        "actions",
        "movement",
        "strength",
        "dexterity",
        "mind",
    )
    list_filter = (ShortShortDescriptionListFilter, "type", "extensions", "is_homebrew")
    search_fields = (
        "name_de",
        "name_en",
        "short_description_de",
        "short_description_en",
    )
    prepopulated_fields = {"slug": ("name_de",)}
    filter_horizontal = ("extensions", "resistances", "weaknesses")

    fieldsets = [
        (
            None,
            {
                "fields": (
                    ("name_de", "name_en"),
                    "slug",
                    "short_description_de",
                    "short_description_en",
                    "type",
                    "wiki_page",
                    "extensions",
                )
            },
        ),
        (
            _("Stats"),
            {
                "fields": (
                    ("health", "movement", "actions"),
                    ("strength", "dexterity", "mind"),
                    ("stress_test_succeeded_stress", "stress_test_failed_stress"),
                )
            },
        ),
        (
            _("Image"),
            {
                "fields": (
                    "image",
                    ("image_copyright", "image_copyright_url"),
                ),
                "classes": ("collapse",),
            },
        ),
        (
            _("Homebrew"),
            {
                "fields": (
                    ("is_homebrew", "keep_as_homebrew"),
                    "created_by",
                    ("homebrew_campaign", "homebrew_character"),
                ),
                "classes": ("collapse",),
            },
        ),
    ]
