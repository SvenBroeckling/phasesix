from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline

from characters.models import Character, CharacterTemplate, Pronoun


class CharacterTemplateInline(TabularInline):
    model = CharacterTemplate


@admin.register(Pronoun)
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


@admin.register(Character)
class CharacterAdmin(ModelAdmin):
    list_display = (
        "name",
        "created_by",
        "pronoun",
        "plot",
        "campaign",
        "npc_campaign",
        "may_appear_on_start_page",
    )
    list_editable = ("may_appear_on_start_page",)
    list_filter = "campaign", "extensions", "plot", "npc_campaign", "created_by"
    search_fields = ("name",)
    inlines = [CharacterTemplateInline]
