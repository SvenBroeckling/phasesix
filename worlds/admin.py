# -*- coding: utf-8 -*-

from django.contrib import admin
from reversion.admin import VersionAdmin

from worlds.models import (
    World,
    WikiPage,
    WikiPageImage,
    WorldSiteConfiguration,
    WikiPageFoeType,
    WikiPageFoeResistanceOrWeakness,
    WikiPageGameValues,
    WikiPageGameAction,
)


class WorldSiteConfigurationInline(admin.StackedInline):
    model = WorldSiteConfiguration


class WorldAdmin(VersionAdmin):
    list_display = ("name_de", "name_en", "is_active", "ordering")
    list_filter = ("is_active",)
    search_fields = ("name_de", "name_en")
    inlines = [WorldSiteConfigurationInline]


class WikiPageImageInline(admin.TabularInline):
    model = WikiPageImage
    extra = 0


class WikiPageGameValuesInline(admin.StackedInline):
    model = WikiPageGameValues
    extra = 0


class WikiPageGameActionInline(admin.StackedInline):
    model = WikiPageGameAction
    extra = 0


class WikiPageAdmin(VersionAdmin):
    list_display = (
        "name_de",
        "name_en",
        "short_name_de",
        "short_name_en",
        "is_active",
        "parent",
        "ordering",
    )
    list_editable = ("is_active", "ordering", "short_name_de", "short_name_en")
    list_filter = ("is_active", "world")
    search_fields = ("name_de", "world__name_de", "name_en", "world__name_en")
    inlines = (WikiPageImageInline, WikiPageGameValuesInline, WikiPageGameActionInline)


class WikiPageGameValuesAdmin(admin.ModelAdmin):
    list_display = ('wiki_page', 'actions', 'walking_range', 'stress_test_succeeded_stress',
                    'stress_test_failed_stress')
    list_editable = 'walking_range', 'stress_test_succeeded_stress', 'stress_test_failed_stress'
    list_filter = "wiki_page__world", "type"


admin.site.register(World, WorldAdmin)
admin.site.register(WikiPage, WikiPageAdmin)
admin.site.register(WikiPageFoeType)
admin.site.register(WikiPageFoeResistanceOrWeakness)
admin.site.register(WikiPageGameValues, WikiPageGameValuesAdmin)
admin.site.register(WikiPageGameAction)
