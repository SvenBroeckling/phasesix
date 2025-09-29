from django.contrib import admin
from unfold.admin import ModelAdmin, StackedInline, TabularInline

from worlds.models import (
    World,
    WikiPage,
    WikiPageImage,
    WikiPageFoeType,
    WikiPageFoeResistanceOrWeakness,
    WikiPageGameValues,
    WikiPageGameAction,
    WorldLeadImage,
    WikiPageEmbedding,
    Language,
    LanguageGroup,
)


class WorldLeadImageInline(TabularInline):
    model = WorldLeadImage
    raw_id_fields = ("character",)


@admin.register(World)
class WorldAdmin(ModelAdmin):
    list_display = ("name_de", "name_en", "is_active", "ordering")
    list_filter = ("is_active",)
    search_fields = ("name_de", "name_en")
    inlines = [WorldLeadImageInline]


class WikiPageImageInline(TabularInline):
    model = WikiPageImage
    extra = 0


class WikiPageGameValuesInline(StackedInline):
    model = WikiPageGameValues
    extra = 0


class WikiPageGameActionInline(StackedInline):
    model = WikiPageGameAction
    extra = 0


class WikiPageEmbeddingInline(TabularInline):
    model = WikiPageEmbedding
    raw_id_fields = ("character",)
    extra = 0


@admin.register(WikiPage)
class WikiPageAdmin(ModelAdmin):
    list_display = (
        "name_de",
        "name_en",
        "short_name_de",
        "short_name_en",
        "is_active",
        "parent",
        "ordering",
    )
    list_editable = (
        "is_active",
        "ordering",
        "short_name_de",
        "short_name_en",
    )
    save_as = True
    list_filter = (
        "is_active",
        "world",
        "wikipagegamevalues__type",
    )
    search_fields = (
        "name_de",
        "world__name_de",
        "name_en",
        "world__name_en",
        "text_de",
        "text_en",
    )
    inlines = (
        WikiPageImageInline,
        WikiPageGameValuesInline,
        WikiPageGameActionInline,
        WikiPageEmbeddingInline,
    )


@admin.register(WikiPageGameValues)
class WikiPageGameValuesAdmin(ModelAdmin):
    list_display = (
        "wiki_page",
        "actions",
        "minimum_roll",
        "health",
        "walking_range",
        "stress_test_succeeded_stress",
        "stress_test_failed_stress",
    )
    list_editable = (
        "actions",
        "minimum_roll",
        "health",
        "walking_range",
        "stress_test_succeeded_stress",
        "stress_test_failed_stress",
    )
    list_filter = "wiki_page__world", "type"
    search_fields = ("wiki_page__name_de", "wiki_page__name_en")


@admin.register(WikiPageGameAction)
class WikiPageGameActionAdmin(ModelAdmin):
    list_display = (
        "wiki_page",
        "name_de",
        "name_en",
        "skill",
        "entity_work_type",
    )
    list_filter = (
        "wiki_page__world",
        "entity_work_type",
    )
    search_fields = ("name_de", "name_en", "wiki_page__name_de", "wiki_page__name_en")


@admin.register(Language)
class LanguageAdmin(ModelAdmin):
    list_display = (
        "name_en",
        "group",
        "extension_string",
        "country_name_en",
        "amount_of_people_speaking",
    )
    search_fields = "name_de", "name_en"
    list_editable = ("group",)
    list_filter = ("extensions",)

    def extension_string(self, obj):
        return ", ".join(e.name for e in obj.extensions.all())


admin.site.register(WikiPageFoeType, ModelAdmin)
admin.site.register(WikiPageFoeResistanceOrWeakness)
admin.site.register(LanguageGroup, ModelAdmin)
