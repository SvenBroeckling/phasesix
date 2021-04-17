from django.contrib import admin

from bestiary.models import FoeType, Foe, FoeResistanceOrWeakness, FoeAction


class FoeActionInline(admin.StackedInline):
    model = FoeAction


class FoeAdmin(admin.ModelAdmin):
    inlines = [FoeActionInline]


admin.site.register(FoeType)
admin.site.register(FoeResistanceOrWeakness)
admin.site.register(Foe)
