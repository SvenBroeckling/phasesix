from django.contrib import admin
from django.utils.translation import gettext_lazy as _
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
    list_editable = ("is_active", "ordering")
    fieldsets = [
        (
            None,
            {
                "fields": (
                    ("name_de", "name_en"),
                    "slug",
                    ("is_active", "is_default", "ordering"),
                    ("extension", "show_in_worlds_overview"),
                )
            },
        ),
        (
            _("Brand"),
            {
                "fields": (
                    ("brand_name_de", "brand_name_en"),
                    ("brand_claim_de", "brand_claim_en"),
                    "brand_logo",
                    "scss_file",
                    "pdf_background",
                )
            },
        ),
        (
            _("Descriptions"),
            {
                "fields": (
                    ("description_1_de", "description_1_en"),
                    ("description_2_de", "description_2_en"),
                    ("description_3_de", "description_3_en"),
                )
            },
        ),
        (
            _("Domains and units"),
            {
                "fields": (
                    ("dns_domain_name", "session_cookie_domain"),
                    ("info_name_cm_de", "info_name_cm_en"),
                    ("info_name_kg_de", "info_name_kg_en"),
                ),
                "classes": ("collapse",),
            },
        ),
        (
            _("Image"),
            {
                "fields": (
                    "image",
                    ("image_copyright", "image_copyright_url"),
                    ("image_focal_x", "image_focal_y"),
                ),
                "classes": ("collapse",),
            },
        ),
        (_("Ownership"), {"fields": ("created_by",), "classes": ("collapse",)}),
    ]


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
    fieldsets = [
        (
            None,
            {
                "fields": (
                    ("name_de", "name_en"),
                    ("short_name_de", "short_name_en"),
                    "slug",
                    ("world", "parent"),
                    ("is_active", "ordering"),
                )
            },
        ),
        (_("Content"), {"fields": (("text_de", "text_en"),)}),
        (
            _("Image"),
            {
                "fields": (
                    "image",
                    ("image_copyright", "image_copyright_url"),
                    ("image_focal_x", "image_focal_y"),
                ),
                "classes": ("collapse",),
            },
        ),
        (_("Ownership"), {"fields": ("created_by",), "classes": ("collapse",)}),
    ]


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
    filter_horizontal = ("resistances", "weaknesses")
    fieldsets = [
        (
            None,
            {
                "fields": (
                    "wiki_page",
                    "type",
                    ("health", "arcana", "protection", "perception"),
                    ("actions", "quickness", "walking_range", "minimum_roll"),
                    ("stress_test_succeeded_stress", "stress_test_failed_stress"),
                    ("resistances", "weaknesses"),
                )
            },
        ),
    ]


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
    fieldsets = [
        (
            None,
            {
                "fields": (
                    "wiki_page",
                    ("name_de", "name_en"),
                    "skill",
                    ("effect_de", "effect_en"),
                    "entity_work_type",
                )
            },
        )
    ]


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
    filter_horizontal = ("extensions",)
    fieldsets = [
        (
            None,
            {
                "fields": (
                    ("name_de", "name_en"),
                    ("country_name_de", "country_name_en"),
                    ("group", "amount_of_people_speaking"),
                    "extensions",
                )
            },
        ),
        (
            _("Homebrew"),
            {
                "fields": (
                    ("is_homebrew", "keep_as_homebrew"),
                    ("homebrew_campaign", "homebrew_character"),
                ),
                "classes": ("collapse",),
            },
        ),
    ]

    def extension_string(self, obj):
        return ", ".join(e.name for e in obj.extensions.all())


admin.site.register(WikiPageFoeType, ModelAdmin)
admin.site.register(WikiPageFoeResistanceOrWeakness)
admin.site.register(LanguageGroup, ModelAdmin)
