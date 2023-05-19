from django.contrib import admin

from pantheon.models import Entity


class EntityAdmin(admin.ModelAdmin):
    list_display = 'name_de', 'name_en', 'wiki_page'
    list_editable = 'wiki_page',


admin.site.register(Entity, EntityAdmin)
