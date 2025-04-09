from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline

from characters.models import Character, CharacterTemplate, Pronoun


class CharacterTemplateInline(TabularInline):
    model = CharacterTemplate


class PronounAdmin(ModelAdmin):
    list_display = (
        "nominative_de",
        "nominative_en",
        "dative_de",
        "dative_en",
        "possessive_de",
        "possessive_en",
        "copula_verb_de",
        "copula_verb_en",
    )


class CharacterAdmin(ModelAdmin):
    list_display = (
        "name",
        "may_appear_on_start_page",
        "created_by",
        "pronoun",
        "campaign",
        "npc_campaign",
    )
    list_editable = (
        "may_appear_on_start_page",
        "campaign",
        "pronoun",
        "npc_campaign",
    )
    list_filter = "campaign", "extensions", "npc_campaign", "created_by"
    search_fields = ("name",)
    inlines = [CharacterTemplateInline]


admin.site.register(Character, CharacterAdmin)
admin.site.register(Pronoun, PronounAdmin)
