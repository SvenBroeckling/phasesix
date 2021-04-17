from django.contrib import admin

from bestiary.models import FoeType, Foe, FoeResistanceOrWeakness, FoeAction


class FoeActionInline(admin.StackedInline):
    model = FoeAction


class FoeAdmin(admin.ModelAdmin):
    inlines = [FoeActionInline]
    list_display = ('name_de', 'name_en', 'type', 'health', 'actions', 'movement', 'minimum_roll')
    list_filter = ('type', 'health', 'actions', 'movement', 'minimum_roll')


admin.site.register(FoeType)
admin.site.register(FoeResistanceOrWeakness)
admin.site.register(Foe, FoeAdmin)
