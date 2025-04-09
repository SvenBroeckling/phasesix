from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline

from horror.models import QuirkModifier, Quirk, QuirkCategory


class QuirkModifierInline(TabularInline):
    model = QuirkModifier


class QuirkAdmin(ModelAdmin):
    inlines = [QuirkModifierInline]
    list_display = ("name_de", "name_en", "category")
    list_filter = ("category",)


admin.site.register(Quirk, QuirkAdmin)
admin.site.register(QuirkCategory, ModelAdmin)
