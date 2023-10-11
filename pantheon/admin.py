from django.contrib import admin

from pantheon.models import Entity, PriestAction, PriestActionRoll, EntityCategory


class EntityAdmin(admin.ModelAdmin):
    list_display = "name_de", "name_en", "wiki_page"
    list_editable = ("wiki_page",)


class PriestActionRollInline(admin.TabularInline):
    model = PriestActionRoll


class PriestActionAdmin(admin.ModelAdmin):
    list_display = "name_de", "name_en", "grace_cost", "work_type"
    list_editable = "grace_cost", "work_type"
    inlines = [PriestActionRollInline]


admin.site.register(EntityCategory)
admin.site.register(Entity, EntityAdmin)
admin.site.register(PriestAction, PriestActionAdmin)
admin.site.register(PriestActionRoll)
