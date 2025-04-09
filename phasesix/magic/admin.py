from django.contrib import admin
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
        "origin",
        "type",
        "variant",
        "range",
        "spell_point_cost",
        "actions",
        "arcana_cost",
    )
    fields = (
        ("name_de", "name_en"),
        ("created_by", "is_homebrew", "homebrew_campaign", "keep_as_homebrew"),
        ("origin", "type", "variant", "shape"),
        ("spell_point_cost", "arcana_cost", "range"),
        "is_ritual",
        (
            "actions",
            "duration_de",
            "duration_en",
            "duration_unit",
            "needs_concentration",
        ),
        ("rules_de", "rules_en"),
        ("quote", "quote_author"),
    )


class SpellTemplateModifierInline(TabularInline):
    model = SpellTemplateModifier


class SpellTemplateAdmin(ModelAdmin):
    list_display = ("name_de", "name_en", "category", "spell_point_cost")
    list_editable = "category", "spell_point_cost"
    list_filter = "spell_point_cost", "category"
    inlines = [SpellTemplateModifierInline]
    fields = (
        ("name_de", "name_en"),
        ("category", "spell_point_cost"),
        ("rules_de", "rules_en"),
        ("quote", "quote_author"),
    )


class SpellTypeAdmin(ModelAdmin):
    list_display = ("name_de", "name_en", "image", "reference_attribute")
    list_editable = ("reference_attribute",)


class BaseSpellInline(TabularInline):
    model = BaseSpell
    fields = ("name_de", "name_en", "arcana_cost", "spell_point_cost")
    show_change_link = True


class SpellOriginAdmin(ModelAdmin):
    list_display = ("name_de", "name_en")
    inlines = [BaseSpellInline]


admin.site.register(SpellOrigin, SpellOriginAdmin)
admin.site.register(BaseSpell, BaseSpellAdmin)
admin.site.register(SpellTemplateCategory, ModelAdmin)
admin.site.register(SpellTemplate, SpellTemplateAdmin)
admin.site.register(SpellTemplateModifier, ModelAdmin)
admin.site.register(SpellShape, ModelAdmin)
admin.site.register(SpellType, SpellTypeAdmin)
admin.site.register(SpellVariant, ModelAdmin)
