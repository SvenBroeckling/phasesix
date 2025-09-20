from django.contrib import admin
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


admin.site.register(QuirkCategory, ModelAdmin)
