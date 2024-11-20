from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline

from pantheon.models import Entity, PriestAction, PriestActionRoll, EntityCategory


class EntityAdmin(ModelAdmin):
    list_display = "name_de", "name_en", "wiki_page"
    list_editable = ("wiki_page",)


class PriestActionRollInline(TabularInline):
    model = PriestActionRoll


class PriestActionAdmin(ModelAdmin):
    list_display = "name_de", "name_en", "grace_cost", "work_type"
    list_editable = "grace_cost", "work_type"
    inlines = [PriestActionRollInline]


admin.site.register(EntityCategory, ModelAdmin)
admin.site.register(Entity, EntityAdmin)
admin.site.register(PriestAction, PriestActionAdmin)
admin.site.register(PriestActionRoll, ModelAdmin)
