# -*- coding: utf-8 -*-

from django.contrib import admin

from worlds.models import World, WikiPage, WikiPage


class WorldAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'ordering')
    list_filter = ('is_active',)
    search_fields = ('name',)


class WikiPageAdmin(admin.ModelAdmin):
    list_display = ('name', 'world', 'is_active', 'parent', 'ordering')
    list_editable = ('is_active', 'ordering')
    list_filter = ('is_active', 'world')
    search_fields = ('name', 'world__name')


admin.site.register(World, WorldAdmin)
admin.site.register(WikiPage, WikiPageAdmin)
