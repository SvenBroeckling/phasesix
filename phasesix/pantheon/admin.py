from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline

from pantheon.models import Entity, PriestAction, PriestActionRoll, EntityCategory


@admin.register(Entity)
class EntityAdmin(ModelAdmin):
    list_display = "name_de", "name_en", "wiki_page"


class PriestActionRollInline(TabularInline):
    model = PriestActionRoll


@admin.register(PriestAction)
class PriestActionAdmin(ModelAdmin):
    list_display = "name_de", "name_en", "grace_cost", "work_type"
    list_editable = "grace_cost", "work_type"
    inlines = [PriestActionRollInline]


admin.site.register(EntityCategory, ModelAdmin)
admin.site.register(PriestActionRoll, ModelAdmin)
