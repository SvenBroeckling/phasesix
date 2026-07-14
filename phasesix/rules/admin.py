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
    filter_horizontal = ("fixed_extensions",)
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
    fieldsets = [
        (
            None,
            {
                "fields": (
                    ("name_de", "name_en"),
                    "identifier",
                    ("type", "ordering"),
                    ("is_active", "is_mandatory"),
                    ("year_range_de", "year_range_en"),
                    ("description_de", "description_en"),
                )
            },
        ),
        (
            _("World configuration"),
            {
                "fields": (
                    "currency_map",
                    "fixed_extensions",
                    "fixed_epoch",
                    "exclusive_languages",
                ),
                "classes": ("collapse",),
            },
        ),
        (
            _("Presentation"),
            {
                "fields": (
                    ("fa_icon_class", "fa_icon_latex"),
                    "image",
                    ("image_copyright", "image_copyright_url"),
                    ("image_focal_x", "image_focal_y"),
                ),
                "classes": ("collapse",),
            },
        ),
        (
            _("Image generation"),
            {
                "fields": ("image_prompt_prefix",),
                "classes": ("collapse",),
            },
        ),
    ]


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
    search_fields = ("name_de", "name_en", "description_de", "description_en")
    list_filter = ("allow_for_reputation", "allow_at_character_creation")
    fieldsets = [
        (None, {"fields": (("name_de", "name_en"), ("description_de", "description_en"))}),
        (_("Presentation"), {"fields": (("bg_color_class", "fg_color_class"), "sort_order")}),
        (_("Availability"), {"fields": (("allow_for_reputation", "allow_at_character_creation"),)}),
    ]


@admin.register(Template)
class TemplateAdmin(ModelAdmin):
    inlines = [TemplateModifierInline, TemplateRequirementInline]
    search_fields = ("name_de", "name_en", "rules_de", "rules_en")
    filter_horizontal = ("extensions",)
    list_display = (
        "name",
        "essential_enabled",
        "cost",
        "category",
        "has_rules",
        "is_mastery",
        "show_rules_in_combat",
        "has_quote",
    )
    list_editable = ("category", "cost", "show_rules_in_combat", "is_mastery")
    list_filter = ("essential_enabled", "extensions", "category", "extensions")
    save_as = True
    fieldsets = [
        (
            None,
            {
                "fields": (
                    ("name_de", "name_en"),
                    ("category", "cost", "is_mastery"),
                    "extensions",
                )
            },
        ),
        (
            _("Rules"),
            {
                "fields": (
                    ("rules_de", "rules_en"),
                    ("show_rules_in_combat", "show_in_attack_dice_rolls"),
                    ("quote", "quote_author"),
                )
            },
        ),
        (
            _("Essential character"),
            {
                "fields": (
                    "essential_enabled",
                    ("essential_description_de", "essential_description_en"),
                    ("essential_benefit_de", "essential_benefit_en"),
                    ("essential_vulnerability_de", "essential_vulnerability_en"),
                    ("essential_facet_de", "essential_facet_en"),
                    ("essential_skills_de", "essential_skills_en"),
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


@admin.register(Attribute)
class AttributeAdmin(ModelAdmin):
    list_display = ("name_de", "name_en", "kind")
    list_editable = ("kind",)
    search_fields = ("name_de", "name_en", "identifier", "description_de", "description_en")
    list_filter = ("kind",)
    fieldsets = [
        (None, {"fields": (("name_de", "name_en"), "identifier", "kind", ("description_de", "description_en"))}),
    ]


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
    search_fields = ("name_de", "name_en", "description_de", "description_en")
    list_filter = ("kind", "is_magical", "extensions")
    filter_horizontal = ("extensions",)
    fieldsets = [
        (None, {"fields": (("name_de", "name_en"), ("description_de", "description_en"), ("kind", "is_magical"), ("reference_attribute_1", "reference_attribute_2"), "extensions")}),
    ]


@admin.register(Knowledge)
class KnowledgeAdmin(ModelAdmin):
    list_display = ("name_de", "name_en", "skill")
    list_editable = ("skill",)
    search_fields = ("name_de", "name_en", "description_de", "description_en")
    list_filter = ("skill", "extensions")
    filter_horizontal = ("extensions",)
    fieldsets = [
        (None, {"fields": (("name_de", "name_en"), ("description_de", "description_en"), "skill", "extensions")}),
    ]


@admin.register(Lineage)
class LineageAdmin(ModelAdmin):
    filter_horizontal = ("extensions",)
    list_display = (
        "name_de",
        "name_en",
        "essential_enabled",
        "template_points",
        "template",
        "base_max_stress",
    )
    list_editable = ("essential_enabled", "base_max_stress")
    fieldsets = [
        (
            None,
            {
                "fields": (
                    ("name_de", "name_en"),
                    ("description_de", "description_en"),
                    ("template", "template_points"),
                    "extensions",
                )
            },
        ),
        (
            _("Character fundamentals"),
            {
                "fields": (
                    ("base_languages", "base_contacts"),
                    ("base_max_health", "base_max_arcana", "base_spell_points"),
                    ("base_actions", "base_minimum_roll"),
                    ("base_bonus_dice", "base_destiny_dice", "base_rerolls"),
                    ("base_evasion", "base_protection"),
                )
            },
        ),
        (
            _("Stress"),
            {
                "fields": (("base_base_stress", "base_max_stress"),),
            },
        ),
        (
            _("Body modifications"),
            {
                "fields": (
                    ("base_bio_strain", "base_energy"),
                    ("base_sockets_head", "base_sockets_torso"),
                    ("base_sockets_left_arm", "base_sockets_right_arm"),
                    ("base_sockets_left_leg", "base_sockets_right_leg"),
                ),
                "classes": ("collapse",),
            },
        ),
        (
            _("Essential character"),
            {
                "fields": (
                    "essential_enabled",
                    ("essential_description_de", "essential_description_en"),
                    ("essential_benefit_de", "essential_benefit_en"),
                    ("essential_vulnerability_de", "essential_vulnerability_en"),
                    ("essential_skills_de", "essential_skills_en"),
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


@admin.register(StatusEffect)
class StatusEffectAdmin(ModelAdmin):
    list_display = ("name_de", "name_en", "fa_icon_class", "is_active")
    list_editable = ("is_active",)
    search_fields = ("name_de", "name_en", "rules_de", "rules_en")
    list_filter = ("is_active", "color_class", "extensions")
    filter_horizontal = ("extensions",)
    fieldsets = [
        (None, {"fields": (("name_de", "name_en"), ("rules_de", "rules_en"), ("is_active", "ordering"), ("fa_icon_class", "color_class"), "extensions")}),
    ]


@admin.register(FoeType)
class FoeTypeAdmin(ModelAdmin):
    list_display = ("name_de", "name_en")
    search_fields = ("name_de", "name_en")
    fieldsets = [(None, {"fields": (("name_de", "name_en"),)})]


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
                    ("resistances", "weaknesses"),
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
                    ("image_focal_x", "image_focal_y"),
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
