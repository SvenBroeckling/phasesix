# -*- coding: utf-8 -*-

from django.contrib import admin
from reversion.admin import VersionAdmin

from worlds.models import World, WikiPage, WikiPageImage


class WorldAdmin(VersionAdmin):
    list_display = ('name_de', 'name_en', 'is_active', 'ordering')
    list_filter = ('is_active',)
    search_fields = ('name_de', 'name_en')


class WikiPageImageInline(admin.TabularInline):
    model = WikiPageImage
    extra = 1


class WikiPageAdmin(VersionAdmin):
    list_display = ('name_de', 'name_en', 'world', 'is_active', 'parent', 'ordering')
    list_editable = ('is_active', 'ordering')
    list_filter = ('is_active', 'world', 'parent')
    search_fields = ('name_de', 'world__name_de', 'name_en', 'world__name_en')
    inlines = (WikiPageImageInline,)


admin.site.register(World, WorldAdmin)
admin.site.register(WikiPage, WikiPageAdmin)
