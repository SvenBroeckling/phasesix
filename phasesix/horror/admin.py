from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin, TabularInline

from horror.models import QuirkModifier, Quirk, QuirkCategory
from portal.admin import ShortDescriptionListFilter


class QuirkModifierInline(TabularInline):
    model = QuirkModifier


@admin.register(Quirk)
class QuirkAdmin(ModelAdmin):
    inlines = [QuirkModifierInline]
    list_display = ("name_de", "name_en", "category")
    list_filter = (
        ShortDescriptionListFilter,
        "category",
    )
    fieldsets = [
        (None, {"fields": (("name_de", "name_en"), "category", ("description_de", "description_en"), ("positive_effects_de", "positive_effects_en"), ("negative_effects_de", "negative_effects_en"))}),
        (_("Homebrew"), {"fields": (("is_homebrew", "keep_as_homebrew"), ("homebrew_campaign", "homebrew_character")), "classes": ("collapse",)}),
    ]


admin.site.register(QuirkCategory, ModelAdmin)
