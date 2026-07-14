from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin, TabularInline

from magic.models import (
    BaseSpell,
    SpellOrigin,
    SpellShape,
    SpellTemplate,
    SpellTemplateCategory,
    SpellTemplateModifier,
    SpellType,
    SpellVariant,
)
from portal.admin import ShortRulesListFilter


@admin.register(BaseSpell)
class BaseSpellAdmin(ModelAdmin):
    list_display = (
        "name_de",
        "name_en",
        "actions",
        "duration_de",
        "duration_en",
        "needs_concentration",
        "spell_point_cost",
        "origin",
        "type",
        "variant",
        "essential_enabled",
    )
    list_editable = (
        "spell_point_cost",
        "origin",
        "actions",
        "duration_de",
        "duration_en",
        "needs_concentration",
    )
    search_fields = ("name_de", "name_en", "rules_de", "rules_en")
    list_filter = (
        ShortRulesListFilter,
        "origin",
        "type",
        "variant",
        "range",
        "spell_point_cost",
        "actions",
        "arcana_cost",
        "essential_enabled",
    )
    fieldsets = [
        (None, {"fields": (("name_de", "name_en"), ("origin", "type", "variant", "shape"), ("spell_point_cost", "arcana_cost", "range"), "is_ritual")}),
        (_("Casting"), {"fields": (("actions", "duration_de", "duration_en", "duration_unit", "needs_concentration"),)}),
        (_("Rules"), {"fields": (("rules_de", "rules_en"), ("quote", "quote_author"))}),
        (_("Essential character"), {"fields": ("essential_enabled",), "classes": ("collapse",)}),
        (_("Homebrew"), {"fields": (("is_homebrew", "keep_as_homebrew"), "created_by", "homebrew_campaign"), "classes": ("collapse",)}),
    ]


class SpellTemplateModifierInline(TabularInline):
    model = SpellTemplateModifier


@admin.register(SpellTemplate)
class SpellTemplateAdmin(ModelAdmin):
    list_display = ("name_de", "name_en", "category", "spell_point_cost")
    list_editable = "category", "spell_point_cost"
    list_filter = "spell_point_cost", "category"
    inlines = [SpellTemplateModifierInline]
    fieldsets = [
        (None, {"fields": (("name_de", "name_en"), ("category", "spell_point_cost"))}),
        (_("Rules"), {"fields": (("rules_de", "rules_en"), ("quote", "quote_author"))}),
    ]


@admin.register(SpellType)
class SpellTypeAdmin(ModelAdmin):
    list_display = ("name_de", "name_en", "image", "reference_attribute")
    list_editable = ("reference_attribute",)
    fieldsets = [
        (None, {"fields": (("name_de", "name_en"), "reference_attribute", "fa_icon_class")} ),
        (_("Image"), {"fields": ("image", ("image_copyright", "image_copyright_url"), ("image_focal_x", "image_focal_y")), "classes": ("collapse",)}),
    ]


class BaseSpellInline(TabularInline):
    model = BaseSpell
    fields = ("name_de", "name_en", "arcana_cost", "spell_point_cost")
    show_change_link = True


@admin.register(SpellOrigin)
class SpellOriginAdmin(ModelAdmin):
    list_display = ("name_de", "name_en", "essential_enabled")
    fieldsets = [
        (None, {"fields": (("name_de", "name_en"), "fa_icon_class", "essential_enabled", "essential_description")}),
        (_("Image"), {"fields": ("image", ("image_copyright", "image_copyright_url"), ("image_focal_x", "image_focal_y")), "classes": ("collapse",)}),
    ]
    inlines = [BaseSpellInline]


admin.site.register(SpellTemplateCategory, ModelAdmin)
admin.site.register(SpellTemplateModifier, ModelAdmin)
admin.site.register(SpellShape, ModelAdmin)
admin.site.register(SpellVariant, ModelAdmin)
