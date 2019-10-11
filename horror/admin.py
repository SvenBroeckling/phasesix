from django.contrib import admin

from horror.models import QuirkModifier, Quirk, QuirkCategory


class QuirkModifierInline(admin.TabularInline):
    model = QuirkModifier


class QuirkAdmin(admin.ModelAdmin):
    inlines = [QuirkModifierInline]


admin.site.register(Quirk, QuirkAdmin)
admin.site.register(QuirkCategory)
