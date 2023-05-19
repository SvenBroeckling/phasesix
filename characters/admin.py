# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from characters.models import Character


class CharacterAdmin(admin.ModelAdmin):
    list_display = 'name', 'may_appear_on_start_page', 'created_by', 'campaign', 'reputation'
    list_editable = 'may_appear_on_start_page',
    list_filter = 'created_by', 'campaign', 'extensions'
    search_fields = 'name',


admin.site.register(Character, CharacterAdmin)
