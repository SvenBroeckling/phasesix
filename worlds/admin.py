# -*- coding: utf-8 -*-

from django.contrib import admin

from worlds.models import World, WikiCategory, WikiPage


class WorldAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'ordering')
    list_filter = ('is_active',)
    search_fields = ('name',)


admin.site.register(World, WorldAdmin)
admin.site.register(WikiCategory)
admin.site.register(WikiPage)
