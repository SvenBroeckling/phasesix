from django.contrib import admin
from reversion.admin import VersionAdmin

from horror.models import QuirkModifier, Quirk, QuirkCategory


class QuirkModifierInline(admin.TabularInline):
    model = QuirkModifier


class QuirkAdmin(VersionAdmin):
    inlines = [QuirkModifierInline]
    list_display = ('name_de', 'name_en', 'category')
    list_filter = 'category',


admin.site.register(Quirk, QuirkAdmin)
admin.site.register(QuirkCategory, VersionAdmin)
